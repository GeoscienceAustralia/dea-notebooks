#include "dtree.h"



TNode* createnode(int arc)
{
    TNode* nd;
    nd=new TNode;
    nd->_arc=arc;
    nd->_paras=NULL;
    nd->_children=NULL;
    return nd;
}

int deletetree(TNode* nd)
{
    int ntype, nc, i;
    if (nd->_children!=NULL)
    {
	nc=nd->_arc+1;
	for(i=0;i<nc;i++)
	{
	    deletetree(nd->_children[i]);
	}
	delete [] nd->_children;
    }
    if (nd->_paras!=NULL)
    {
	delete [] nd->_paras;
    }
    delete nd;
    return 0;
}

int dfvarmapping(TNode** dforest, int fstsize, size_t* sels)
{
    int i;
    for(i=0;i<fstsize;i++)
    {
	varmapping(dforest[i], sels);
    }
    return 0;
}


int varmapping(TNode* nd, size_t* sels)
{
    int vid, nc, i;
    
    if (nd->_children!=NULL)
    {
	vid=nd->_vid;
	nd->_vid=sels[vid];
	nc=nd->_arc+1;
	for(i=0;i<nc;i++)
	{
	    varmapping(nd->_children[i], sels);
	}
    }
    return 0;
}

double mum_msglen(size_t* counts, int arc)
{
    double lpc, sum, msg;
    int i;

    lpc=1.0;
    msg=0;
    sum=lpc*arc;
    for(i=0;i<arc;i++)
    {
	sum+=counts[i];
    }

    for(i=0;i<arc;i++)
    {
	msg+=-counts[i]*log((counts[i]+lpc)/sum);
    }

    return msg;
}



double cut_msglen(size_t* lf_labc, size_t* rt_labc, int arc)
{

    long i;

    return mum_msglen(lf_labc, arc) + mum_msglen(rt_labc, arc);  

}




// Find single cut point for the array data
// cudcuts  -- number of candidate cut points to search
// rndrng -- randomness, 0 means return the best cut, 1 means totally random selection of the cut point
// num -- number of data point in array data

long findunisplit(double* data, int* labs, long num, int arc, long cndcuts, double rndrng, double& cutval, size_t* sts)
{
    long i, j, parts, seg, mid, shlistnum, pick, lastmid;

    size_t *cutsts;
    double* msg, *cutpoints;
    size_t* lf_labc, *rt_labc;
    long idx;
    int lb;
    double nullmsg, minmsg;


    gsl_rng* rng;

    //cout<<"arc="<<arc<<" cndcuts="<<cndcuts<<endl;
    msg= new double[cndcuts];
    cutpoints= new double[cndcuts];
    cutsts= new size_t[cndcuts];
    lf_labc=new size_t[arc+1];
    rt_labc=new size_t[arc+1];


    rng=gsl_rng_alloc(gsl_rng_taus);
    gsl_rng_set(rng, time(NULL));


    parts=cndcuts+1;

    gsl_sort_index(sts, data, 1, num);


    seg = num/parts;
    for(i=0;i<arc+1;i++)
    {
	lf_labc[i]=0;
	rt_labc[i]=0;
    }

    for(i=0;i<num;i++)
    {
	//cout<<"i="<<i;
	lb=labs[i];
	//cout<<" labs="<<labs[i]<<endl;;
	rt_labc[lb]++;
    }

    nullmsg=mum_msglen(rt_labc, arc);

    mid=0;
    for (i=0;i<cndcuts;i++)
    {
	lastmid=mid;
	mid+=seg;
	idx=sts[mid];
	cutpoints[i]=data[idx];
	for(j=lastmid;j<mid;j++)
	{
	    idx=sts[j];
	    lb=labs[idx];
	    lf_labc[lb]++;
	    rt_labc[lb]--;
	    msg[i]=cut_msglen(lf_labc, rt_labc, arc);
	}
    }

    gsl_sort_index(cutsts, msg, 1, cndcuts);


    idx=cutsts[0];
    minmsg=msg[idx];
    if (nullmsg<minmsg) // No cut is found
    {
	mid = -1;
	cutval=0;
    }
    else 
    {
	shlistnum = (long) (cndcuts*rndrng + 1);
	pick = gsl_rng_uniform(rng)*shlistnum; 
	idx=cutsts[pick];
	cutval=cutpoints[idx];
	mid=(idx+1)*seg;
    }

    gsl_rng_free(rng);
    delete [] cutsts;
    delete [] msg;
    delete [] cutpoints;
    delete [] lf_labc;
    delete [] rt_labc;


    return mid;

}


int est_multinomial(int* glabs, size_t* idxlist, long bidx, long eidx, int arc, double*& paras)
{

    long i;
    int lb, parts;
    size_t idx;
    double sum, lpc;

    parts=arc+1;
    paras=new double[parts];

    lpc=1.0;
    sum=lpc*parts;
    for(i=0;i<parts;i++)
    {
	paras[i]=0;
    }


    for(i=bidx;i<eidx;i++)
    {
	idx=idxlist[i];
	lb=glabs[idx];
	paras[lb]+=1.0;
    }


    for(i=0;i<parts;i++)
    {
	sum+=paras[i];
    }

    for(i=0;i<parts;i++)
    {
	paras[i]/=sum;
    }

    return 0;
}

// Build a (semi-)random tree
//
TNode* buildtree(double* raw, int nd,  int* glabs, long num, size_t* idxlist, int arc, long cndcuts, double rndrng, int cur_depth, int maxdepth)
{
    long i, j, mid, cc, ss;
    int pick, parts, swt, next_depth;
    size_t idx;

    double* data;
    double cutval;
    size_t *sts;
    size_t** subidxlist;
    int* labs;
    long *subnum;
    long mindata;



    TNode* root, *child;
    gsl_rng* rng;



    rng=gsl_rng_alloc(gsl_rng_taus);
    gsl_rng_set(rng, time(NULL));
    data= new double[num];
    sts=new size_t[num];
    labs=new int[num];

    mindata = 12;
    // create root node
    root = createnode(arc);
    // Randomly pick one input variable

    pick =(int) (gsl_rng_uniform(rng)*nd); 

    for(i=0;i<num;i++)
    {
	idx=idxlist[i];
	data[i] = raw[idx*nd+pick];
	labs[i] = glabs[idx];

//	cout<<"i="<<i<<" idx="<<idx;
//	cout<<" labs="<<labs[i]<<endl;;
    }

    root->_vid=pick;
    if (num < mindata)
    {
	est_multinomial(glabs, idxlist, 0, num, arc, root->_paras);
    }
    else
    {
	mid = findunisplit(data, labs, num, arc, cndcuts, rndrng, cutval, sts);

	if (mid<0) // Can not find any valid cut point
	{
	    est_multinomial(glabs, idxlist, 0, num, arc, root->_paras);
	}
	else  // split the data, create 2 new nodes
	{
	    root->_children =new TNode*[2];
	    root->_arc=1;
	    root->_paras = new double[2];
	    root->_paras[0]=cutval;

	    next_depth=cur_depth+1;
	    parts=2;

	    subidxlist = new size_t*[parts];
	    subnum= new long[parts];
	    subnum[0]=mid;
	    subnum[1]=num - mid;

	    for(i=0;i<parts;i++)
	    {
		subidxlist[i] = new size_t[subnum[i]];
	    }
	    cc=0;
	    ss=0;
	    for(i=0;i<num;i++)
	    {
		idx=sts[i];
		if (i<mid)
		{
		    subidxlist[0][cc]=idxlist[idx];
		    cc++;
		}
		else
		{
		    subidxlist[1][ss]=idxlist[idx];
		    ss++;
		}
	    }

	    if (next_depth>=maxdepth)  
	    {
		for(i=0;i<parts;i++)
		{
		    root->_children[i] = createnode(arc);
		}
		for(i=0;i<parts;i++)
		{
		    child = root->_children[i];
		    est_multinomial(glabs, subidxlist[i], 0, subnum[i], arc, child->_paras);
		}
	    }
	    else
	    {
		for(i=0;i<parts;i++)
		{
		    root->_children[i] = buildtree(raw, nd,  glabs, subnum[i], subidxlist[i], arc, cndcuts, rndrng, next_depth, maxdepth);
		}
	    }

	    for(i=0;i<parts;i++)
	    {
		delete [] subidxlist[i];
	    }

	    delete [] subidxlist;
	    delete [] subnum;

	}
    }

    gsl_rng_free(rng);
    delete [] data;
    delete [] labs;
    delete [] sts;
    return root;
}

TNode* findleaf(TNode* root, double* data, int nd, long idx)
{
    int i, vid, arc, nxt;
    double val;

    if (root->_children==NULL)
    {
	return root;
    }

    vid = root->_vid;
    arc = root->_arc;
    val = data[idx*nd+vid];

    nxt=arc;
    for(i=0;i<arc;i++)
    {
	if (val<root->_paras[i])
	{
	    nxt=i;
	    break;
	}
    }
    return findleaf(root->_children[nxt], data, nd, idx);
}


int dtclassifier(TNode* root, double* data, int nd, long idx, double*& cdis)
{
    int i, arc, maxcls;
    double maxval;

    TNode* leaf;

    leaf= findleaf(root, data, nd, idx);

    arc=leaf->_arc;
    cdis=leaf->_paras;
    maxval=cdis[0];
    maxcls=0;
    for(i=1;i<arc;i++)
    {
	if (cdis[i]>maxval)
	{
	    maxval=cdis[i];
	    maxcls=i;
	}
    }
    //cout<<"leaf="<<leaf<<" maxcls="<<maxcls<<" cdis0="<<cdis[0]<<" cdis1="<<cdis[1]<<endl;
    return maxcls;
}

int writeaforest(string ofname, TNode** dforest, size_t ss)
{

    size_t i;
    ofstream fout;


    if (ss<=0)
    {
	cout<<"No trees in the forest."<<endl;
	return -1;
    }
    fout.open(ofname.c_str(), ios::binary);
    if (!fout.good())
    {
	cout<<"Can not open the output file "<<ofname<<endl;
    }
    for(i=0;i<ss;i++)
    {
	writeatree(fout, dforest[i]);
    }
    fout.close();
    return 0;

}


int writeaforest(string ofname, vector<TNode*>& dforest)
{

    size_t i, ss;
    ofstream fout;

    ss=dforest.size();

    if (ss<=0)
    {
	cout<<"No trees in the forest."<<endl;
	return -1;
    }
    fout.open(ofname.c_str(), ios::binary);
    if (!fout.good())
    {
	cout<<"Can not open the output file "<<ofname<<endl;
    }
    for(i=0;i<ss;i++)
    {
	writeatree(fout, dforest[i]);
    }
    fout.close();
    return 0;

}

int writeatree(ofstream& fout, TNode* root)
{
    
    double leaf, internal, dvid, darc;
    int ns, i;

    internal=1.0;
    leaf=0;

    if (root->_children!=NULL) //internal node
    {
	fout.write((char*)&internal, sizeof(double));
	darc=(double)root->_arc;
	fout.write((char*)&darc, sizeof(double));
	dvid=(double)root->_vid;
	fout.write((char*)&dvid, sizeof(double));
	fout.write((char*)root->_paras, root->_arc*sizeof(double));
	ns=root->_arc+1;
	for(i=0;i<ns;i++)
	{
	    writeatree(fout, root->_children[i]);
	}
    }
    else //leaf node
    {
	fout.write((char*)&leaf, sizeof(double));
	darc=(double)root->_arc;
	fout.write((char*)&darc, sizeof(double));
	ns=root->_arc+1;
	fout.write((char*)root->_paras, ns*sizeof(double));
    }
    return 0;
}

int readatree(string ifname, TNode*& root)
{
    ifstream fin;
    size_t pos, length, ss;
    int nodetype;
    double *data;

    fin.open(ifname.c_str(), ios::binary);

    if (!fin.good())
    {
	cout<<"Can not open tree file, exit ..."<<endl;
	root=NULL;
	return -1;
    }
    
    fin.seekg(0, ios::end);
    length=fin.tellg();
    fin.seekg(0, ios::beg);
    
    ss=length/sizeof(double);
    data = new double[ss];

    fin.read((char*)data, ss*sizeof(double));
    fin.close();

    pos=0;
    root=readanode(data, pos);


    return 0;
}

int readaforest(string ifname, vector<TNode*>& dforest)
{
    ifstream fin;
    size_t pos, length, ss;
    int nodetype;
    double *data;
    TNode* root;

    fin.open(ifname.c_str(), ios::binary);

    if (!fin.good())
    {
	cout<<"Can not open tree file, exit ..."<<endl;
	root=NULL;
	return -1;
    }
    
    fin.seekg(0, ios::end);
    length=fin.tellg();
    fin.seekg(0, ios::beg);
    
    ss=length/sizeof(double);
    data = new double[ss];

    fin.read((char*)data, ss*sizeof(double));
    fin.close();

    pos=0;
    do
    {
	root=readanode(data, pos);
	dforest.push_back(root);
    }while(pos<ss);

    delete [] data;
    return 0;
}

TNode* readanode(double* data, size_t& pos)
{
    TNode* root;
    int arc, i, ns, nodetype;

    nodetype=(int)data[pos];
    pos++;
    arc=(int)data[pos];
    pos++;
    root=createnode(arc);
    if (nodetype==1)  // internal node
    {
	root->_vid=(int)data[pos];
	pos++;
	root->_paras=new double[arc];
	for(i=0;i<arc;i++)
	{
	    root->_paras[i]=data[pos];
	    pos++;
	}
	ns=arc+1;
	root->_children=new TNode*[ns];
	for(i=0;i<ns;i++)
	{
	    root->_children[i]=readanode(data,pos);
	}
    }
    else // leaf node
    {
	ns=arc+1;
	root->_paras=new double[ns];
	for(i=0;i<ns;i++)
	{
	    root->_paras[i]=data[pos];
	    pos++;
	}
    }
    return root;
}

int deleteforest(TNode** forest, int fstsize)
{
    size_t i,ss;

    ss=fstsize;
    if (ss>0)
    {
	for(i=0;i<ss;i++)
	{
	    deletetree(forest[i]);
	}
    }
    delete [] forest;
    return ss;
}

int deleteforest(vector<TNode*>& forest)
{
    size_t i, ss;

    ss=forest.size();
    if (ss>0)
    {
	for(i=0;i<ss;i++)
	{
	    deletetree(forest[i]);
	}
    }
    forest.clear();
    return ss;
}

int forestclassifier(TNode** dforest, int fstsize, double* data, int nd, long idx, double*& clsd)
{
    double* cdis;
    int i, j, enscls,  ns;


    //cout<<"fstsize="<<fstsize<<" ans="<<nd<<endl;
    if (fstsize<=0)
    {
	return -1;
    }

    ns=2;
    //Only work for binary class at the moment
    clsd=new double[ns];
    
    for(i=0;i<ns;i++)
    {
	clsd[i]=0;
    }

    for(j=0;j<fstsize;j++)
    {
	//cout<<j<<", ";
	dtclassifier(dforest[j], data, nd, idx, cdis);
	for(i=0;i<ns;i++)
	{
	    clsd[i]+=cdis[i];
	}
    }

    for(i=0;i<ns;i++)
    {
	clsd[i]/=fstsize;
    }
    

    //cout<<endl;
    if (clsd[0]>clsd[1])
    {
	enscls=0;
    }
    else
    {
	enscls=1;
    }

    return enscls;

}




int forestclassifier(vector<TNode*>& dforest, double* data, int nd, long idx, double*& clsd)
{
    double* cdis;
    int i, j, enscls, fstsize, ns;



    fstsize=dforest.size();
    //cout<<"fstsize="<<fstsize<<" ans="<<nd<<endl;
    if (fstsize<=0)
    {
	return -1;
    }

    ns=2;
    //Only work for binary class at the moment
    clsd=new double[ns];
    
    for(i=0;i<ns;i++)
    {
	clsd[i]=0;
    }

    for(j=0;j<fstsize;j++)
    {
	//cout<<j<<", ";
	dtclassifier(dforest[j], data, nd, idx, cdis);
	for(i=0;i<ns;i++)
	{
	    clsd[i]+=cdis[i];
	}
    }

    for(i=0;i<ns;i++)
    {
	clsd[i]/=fstsize;
    }
    

    //cout<<endl;
    if (clsd[0]>clsd[1])
    {
	enscls=0;
    }
    else
    {
	enscls=1;
    }

    return enscls;

}


int classifyaset(vector<TNode*>& dforest, double* data, int nd, long pnum, float*& pr)
{

    long i, j;
    double* clsd;
    int ns;

    ns=2;

    pr=new float[pnum*ns];

#pragma omp parallel private(i, clsd)
#pragma omp for schedule(dynamic) nowait
    
    for(i=0;i<pnum;i++)
    {
	forestclassifier(dforest, data, nd, i, clsd);
	for(j=0;j<ns;j++)
	{
	    pr[i*ns+j]=clsd[j];
	}
	delete [] clsd;    
    }

    return 0;
}

int classifyaset(TNode** dforest, size_t fstsize, double* data, int nd, long pnum, float*& pr)
{

    long i, j;
    double* clsd;
    int ns;

    ns=2;

    pr=new float[pnum*ns];

#pragma omp parallel private(i, clsd)
#pragma omp for schedule(dynamic) nowait
    
    for(i=0;i<pnum;i++)
    {
	forestclassifier(dforest, fstsize, data, nd, i, clsd);
	for(j=0;j<ns;j++)
	{
	    pr[i*ns+j]=clsd[j];
	}
	delete [] clsd;    
    }

    return 0;
}

