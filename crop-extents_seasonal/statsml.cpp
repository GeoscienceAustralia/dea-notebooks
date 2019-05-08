#include "statsml.h"

// Calculate the covariance matrix of  a set of data, the data is specified by matrix X, 
// the data vectors are placed as row vectors in X so
// if each data has m features and there are total n data in the set, then
// X is an  n x m matrix, output matrix will be an m x m symmetric matrix

int covmatrix(gsl_matrix* blk, gsl_matrix*& cvm)
{
    cvm=covmatrix_row(blk);
    return 0;
}

// Calculate the covariance and correlation matrix of data, the data is given by matrix blk, each of whose columns represents 
// a set of values from one input variable. So the let ts = number of input variables which us  the number of columns of blk, the function
// return two ts by ts matrices  

/*
   int covmatrix(gsl_matrix* blk, gsl_matrix*& cvm, gsl_matrix*& crm)
   {
   int i, j, k, ts, psnum;
   double p;
   double* ptri, *ptrj;
   gsl_vector *vptri, *vptrj;
   gsl_vector_view blk_vvi, blk_vvj;

   psnum=blk->size1;
   ts=blk->size2;

//gsl_matrix_free(cvm);
//gsl_matrix_free(crm);

cvm=gsl_matrix_alloc(ts,ts);
crm=gsl_matrix_alloc(ts,ts);

vptri=gsl_vector_alloc(psnum);	
vptrj=gsl_vector_alloc(psnum);	

for (i=0;i<ts;i++)
{
for(j=i;j<ts;j++)
{
blk_vvi=gsl_matrix_column(blk,i);
blk_vvj=gsl_matrix_column(blk,j);
gsl_vector_memcpy(vptri, &blk_vvi.vector);
ptri=gsl_vector_ptr(vptri,0);
gsl_vector_memcpy(vptrj, &blk_vvj.vector);
ptrj=gsl_vector_ptr(vptrj,0);
p=gsl_stats_covariance(ptri,1,ptrj,1,psnum);
gsl_matrix_set(cvm,i,j,p);
gsl_matrix_set(cvm,j,i,p);
p=gsl_stats_correlation(ptri,1,ptrj,1,psnum);
gsl_matrix_set(crm,i,j,p);
gsl_matrix_set(crm,j,i,p);
}
}

gsl_vector_free(vptri);
gsl_vector_free(vptrj);

return 0;
}
 */

// Calculate the Mahalanobis distance between vector v1 and v2, icvm store the INVERT of the covariance matrix 
double mahdistance(gsl_vector* v1, gsl_vector* v2, gsl_matrix* icvm)
{
    int i, j, ss;
    double dd;
    gsl_vector* dtv, *ptv;

    ss=v1->size;

    dtv=gsl_vector_alloc(ss);	
    ptv=gsl_vector_calloc(ss);	

    gsl_vector_memcpy(dtv, v1);    
    gsl_vector_sub(dtv,v2);

    gsl_blas_dgemv(CblasNoTrans, 1.0, icvm, dtv, 0, ptv);
    gsl_blas_ddot(dtv, ptv, &dd);

    gsl_vector_free(dtv);
    gsl_vector_free(ptv);

    return dd;
}

// Calculate the core of each class from instances in ma, each instance is stored at each row 
int calcores(gsl_matrix* cores, int* acls, gsl_matrix* ma, int nc)
{
    int i, irow, cls, band;
    int* counts;

    gsl_vector** corelists;
    gsl_vector* vc;

    irow=ma->size1;
    band=ma->size2;
    counts=new int[nc];
    corelists=new gsl_vector* [nc];
    vc = gsl_vector_alloc(band);

    for(i=0;i<nc;i++)
    {
	corelists[i]=gsl_vector_calloc(band);
	counts[i]=0;
    }


    for(i=0;i<irow;i++)
    {
	cls=acls[i];
	gsl_matrix_get_row(vc, ma, i);
	gsl_vector_add(corelists[cls], vc);
	counts[cls]++;
    }

    for(i=0;i<nc;i++)
    {
	gsl_vector_scale(corelists[i], 1.0/counts[i]);
	gsl_matrix_set_row(cores, i, corelists[i]);
    }


    for(i=0;i<nc;i++)
    {
	gsl_vector_free(corelists[i]);
    }

    gsl_vector_free(vc);

    delete [] corelists;
    delete [] counts;

    return 0;
}

//Calculate the score for a cluster solution, which is the sum of Mahalanobis 
//distance between vectors from different cluster minus  the sum of Mahalanobis distance vectors from the same cluster
double clusterscores(gsl_matrix* data, gsl_matrix* icvm, int** signtab)
{
    int i, j, irow, band;
    double scores;	

    gsl_vector **v;

    irow=data->size1;
    band=data->size2;

    v=new gsl_vector*[irow];
    for(i=0;i<irow;i++)
    {
	v[i]=gsl_vector_alloc(band);
	gsl_matrix_get_row(v[i], data, i);
    }

    scores=0;
    for(i=0;i<irow-1;i++)
    {
	for(j=i+1;j<irow;j++)
	{
	    scores+=signtab[i][j]* mahdistance(v[i], v[j], icvm);
	}
    }	

    for(i=0;i<irow;i++)
    {
	gsl_vector_free(v[i]);
    }

    delete [] v;

    return scores;
}

// Return the inverse of a matrix
gsl_matrix* invmatrix(gsl_matrix* cvm)
{
    int i, j, irow, signum;

    gsl_matrix *icvm, *LU; 
    gsl_permutation* perm;

    irow=cvm->size1;
    // must to square matrix
    if (irow!=cvm->size2)
    {
	return NULL;
    }
    icvm=gsl_matrix_alloc(irow, irow);  
    LU=gsl_matrix_alloc(irow, irow); 
    perm=gsl_permutation_alloc(irow);

    gsl_matrix_memcpy(LU, cvm);
    gsl_linalg_LU_decomp(LU, perm, &signum);
    gsl_linalg_LU_invert(LU, perm, icvm);

    gsl_matrix_free(LU); 
    gsl_permutation_free(perm);
    return icvm;
}

double tryoneprojection(gsl_matrix* ma, int** signtab,  gsl_matrix* mp)
{   
    int i, j, irow, nb;
    double merit;

    gsl_matrix *mn, *cvm, *icvm; 

    irow=ma->size1;
    nb=mp->size2;	

    mn=gsl_matrix_alloc(irow, nb); // The data matrix in the new feature space

    gsl_matrix_set_zero(mn);
    gsl_blas_dgemm(CblasNoTrans, CblasNoTrans, 1.0, ma, mp, 1.0, mn);

    covmatrix(mn, cvm);

    icvm=invmatrix(cvm);
    merit=clusterscores(mn, icvm, signtab);

    gsl_matrix_free(mn);
    gsl_matrix_free(cvm);
    gsl_matrix_free(icvm);

    return merit;
}


// vary the (x, y) coefficient of the projection matrix N times to find the optimal projection matrix mp which maximise the merit
double trymultiprojection(gsl_matrix* ma, int** signtab,  gsl_matrix* mp, int N, int x, int y, double& ut, double& sigma, double tail)
{
    int i, j, fb, nb, M, ind, xx, yy;
    double* merits, *au;
    double u, solution, ssig;
    size_t* sts;
    gsl_matrix** mpclist;
    gsl_rng* rng;


    if (N<=0)
    {
	return -1;
    }

    rng=gsl_rng_alloc(gsl_rng_taus);
    gsl_rng_set(rng, time(NULL));

    fb=mp->size1;
    nb=mp->size2;
    merits=new double[N];
    au=new double[N];
    sts=new size_t [N];
    mpclist=new gsl_matrix* [N];

    for(i=0;i<N;i++)
    {
	mpclist[i]=gsl_matrix_alloc(fb, nb);		    
	gsl_matrix_memcpy(mpclist[i], mp);
    }

    if (x<0 || y<0)
    {
	for(i=0;i<N;i++)
	{
	    M=(int)gsl_ran_exponential(rng, 8)+2;

	    for(j=0;j<M;j++)
	    {
		xx=(int) (gsl_rng_uniform(rng)*fb);
		yy=(int) (gsl_rng_uniform(rng)*nb);
		u=gsl_matrix_get(mp, xx, yy);
		au[i]= gsl_ran_gaussian(rng, 2.0)+u;
		gsl_matrix_set(mpclist[i], xx, yy, au[i]);
	    }
	}
    }
    else
    {

	u=gsl_matrix_get(mp, x, y);
	for(i=0;i<N;i++)
	{
	    au[i]= gsl_ran_gaussian(rng, sigma)+u;
	    //au[i]= gsl_ran_gaussian(rng, 2.0)+u;
	    gsl_matrix_set(mpclist[i], x, y, au[i]);
	}
    }

#pragma omp parallel private(i) firstprivate(N)
#pragma omp for schedule(dynamic,50) nowait

    for(i=0;i<N;i++)
    {
	merits[i]=tryoneprojection(ma, signtab,  mpclist[i]);	    
    }

    gsl_sort_index(sts, merits, 1, N);
    if (x<0 || y<0)
    {
	ind=sts[N-1];
	gsl_matrix_memcpy(mp, mpclist[ind]);
	solution=merits[ind];    	
    }
    else
    {
	M=(int)((1-tail)*N);	
	ut=0;
	for(i=M;i<N;i++)
	{
	    ind=sts[i];
	    ut+=au[ind];
	}
	ut/=(N-M);
	ssig=0;
	for(i=M;i<N;i++)
	{
	    ind=sts[i];
	    ssig+=(au[ind]-ut)*(au[ind]-ut);
	}
	ssig/=(N-M-1);
	ind=sts[M+1];
	ut=gsl_matrix_get(mpclist[ind], x, y);
	sigma=sqrt(ssig);
	solution=merits[M];	    

	// Get the best one 
	// ind=sts[N-1];
	// ut=gsl_matrix_get(mpclist[ind], x, y);
	// solution=merits[ind];    	
    }

    for(i=0;i<N;i++)
    {
	gsl_matrix_free(mpclist[i]);		    
    }
    gsl_rng_free(rng);
    delete [] merits;
    delete [] au;
    delete [] sts;
    delete [] mpclist;

    return solution;
}


float** dataproj(float** data,  gsl_matrix* mp, int irow)
{
    int i, j, fb, ind, nb;
    float** pmp;
    gsl_vector* v1, *v2;

    fb=mp->size1;
    nb=mp->size2;
    v1=gsl_vector_alloc(fb);
    v2=gsl_vector_alloc(nb);
    creatematrix(pmp, irow, nb);
    for(j=0;j<irow;j++)
    {
	for(i=0;i<fb;i++)
	{
	    gsl_vector_set(v1, i, data[j][i]);
	}
	gsl_vector_set_zero(v2);
	gsl_blas_dgemv(CblasTrans, 1, mp, v1, 0, v2);
	for(i=0;i<nb;i++)
	{
	    pmp[j][i]=gsl_vector_get(v2, i);
	}
    }

    gsl_vector_free(v1); 
    gsl_vector_free(v2); 

    return pmp;
}


int KNNclassifyraw(float* data, gsl_matrix* mp, gsl_matrix* tpoints, int* acls,  gsl_matrix* icvm, int M, int K, double*& mc)
{

    int i, fb, ind, nb;

    gsl_vector* v1, *v2;

    fb=mp->size1;
    nb=mp->size2;
    v1=gsl_vector_alloc(fb);
    v2=gsl_vector_alloc(nb);
    for(i=0;i<fb;i++)
    {
	gsl_vector_set(v1, i, data[i]);
    }
    gsl_vector_set_zero(v2);
    gsl_blas_dgemv(CblasTrans, 1, mp, v1, 0, v2);
    ind = KNNclassify(v2, tpoints, acls,  icvm,  M,  K, mc);
    gsl_vector_free(v1); 
    gsl_vector_free(v2); 
    return ind;
}

// K Nearest Neighbour classifier
int KNNclassify(gsl_vector* v1, gsl_matrix* tpoints, int* acls,  gsl_matrix* icvm, int M, int K, double*& mc)
{
    int i, irow, ind, fb;
    double* mdis;
    size_t* sts;

    gsl_vector* v2;
    irow=tpoints->size1;
    fb=v1->size;
    v2=gsl_vector_alloc(fb);
    mdis=new double[irow];
    mc=new double[M];
    sts=new size_t[irow];

    for(i=0;i<irow;i++)
    {
	gsl_matrix_get_row( v2, tpoints, i);
	mdis[i]=mahdistance(v1, v2, icvm);
    }

    gsl_sort_index(sts, mdis, 1, irow);

    for(i=0;i<M;i++)
    {
	mc[i]=0;
    }

    for(i=0;i<K;i++)
    {
	ind=sts[i];
	mc[acls[ind]]++;
	//	cout<<"mdis="<<mdis[ind]<<"cls="<<acls[ind]<<" ind="<<ind<<endl;
    }
    //    cout<<"********************************************"<<endl;
    ind=gsl_stats_max_index(mc, 1, M);

    delete [] mdis;
    delete [] sts;

    gsl_vector_free(v2); 
    return ind;
}

int findK(gsl_matrix* tpoints, int* acls,  gsl_matrix* icvm, int M, int maxK)
{
    int i, irow, fb, j, ind, k;
    double* errs, *mdis, *mc;
    size_t* sts;
    gsl_vector *v1, *v2;

    irow=tpoints->size1;
    fb=tpoints->size2;


    v1=gsl_vector_alloc(fb);
    v2=gsl_vector_alloc(fb);

    errs=new double[maxK];
    mdis=new double[irow];
    mc=new double[M];
    sts=new size_t[irow];
    for(i=0;i<maxK;i++)
    {
	errs[i]=0;
    }

    for(k=1;k<maxK;k++)
    {
	for(i=0;i<irow;i++)
	{
	    gsl_matrix_get_row( v1, tpoints, i);
	    for(j=0;j<irow;j++)
	    {
		gsl_matrix_get_row(v2, tpoints, j);
		if (i!=j)
		{
		    mdis[j]=mahdistance(v1, v2, icvm);
		}
		else
		{
		    mdis[j]=DBL_MAX;
		}
	    }
	    gsl_sort_index(sts, mdis, 1, irow);
	    for(j=0;j<M;j++)
	    {
		mc[j]=0;
	    }
	    for(j=0;j<k;j++)
	    {
		ind=sts[j];
		mc[acls[ind]]++;
	    }
	    ind=gsl_stats_max_index(mc, 1, M);
	    if (ind!=acls[i])
	    {
		errs[k]++;
	    }
	}
	//cout<<"Err["<<k<<"]="<<errs[k]<<endl;
    }

    ind=gsl_stats_min_index(errs, 1, maxK);


    delete [] mdis;
    delete [] sts;
    delete [] mc;
    delete [] errs;

    gsl_vector_free(v1); 
    gsl_vector_free(v2); 

    return ind+1;
}

int findicvm(gsl_matrix* ma, gsl_matrix* icvm)
{
    int i;
    gsl_matrix* cvm, *picvm;


    covmatrix(ma, cvm);

    picvm= invmatrix(cvm);
    gsl_matrix_memcpy(icvm, picvm);

    gsl_matrix_free(cvm);
    gsl_matrix_free(picvm);
    return 0;
}


// x -- row index of the top left conner
// y -- column index of the top left conner
// irow -- # of row in the block
// icol -- # of columns in the block
// *ida -- array storing the order of pixel index
// rs --- # of pixels in one row of the original file
// bsthod -- maximum size of a block that can be unmix in one round
int genorders(int x, int y, int irow, int icol, int* ida, int& pc, int rs, int bsthod)
{

    int i, pnum, xf, yf, ind, x1, x2, y1, y2;
    gsl_rng* rng;
    size_t* sts;
    double* u;

    pnum=irow*icol;
    if (pnum<bsthod)
    {
	rng=gsl_rng_alloc(gsl_rng_taus);
	gsl_rng_set(rng, time(NULL));
	sts=new size_t[pnum];
	u=new double[pnum];

	for(i=0;i<pnum;i++)
	{
	    u[i]=gsl_rng_uniform(rng);	
	}
	gsl_sort_index(sts,u, 1,pnum);
	for(i=0;i<pnum;i++)
	{
	    ind=sts[i];
	    xf=(int)floor(((double)ind)/icol);
	    xf+=x;
	    yf=ind%icol;
	    yf+=y;
	    ind=xf*rs+yf;
	    ida[pc]=ind;
	    pc++;
	}
	delete [] u;
	delete [] sts;
	gsl_rng_free(rng);
	return 0;
    }
    else
    {
	x1=irow/3;
	x2=irow*2/3;
	y1=icol/3;
	y2=icol*2/3;

	genorders(x+x1, y+y1, x2-x1, y2-y1, ida, pc, rs, bsthod);
	genorders(x+x2, y+y1, irow-x2, y2-y1, ida, pc, rs, bsthod);
	genorders(x+x2, y+y2, irow-x2, icol-y2, ida, pc, rs, bsthod);
	genorders(x+x1, y+y2, x2-x1, icol-y2, ida, pc, rs, bsthod);
	genorders(x, y+y2, x1, icol-y2, ida, pc, rs, bsthod);
	genorders(x, y+y1, x1, y2-y1, ida, pc, rs, bsthod);
	genorders(x, y, x1, y1, ida, pc, rs, bsthod);
	genorders(x+x1, y, x2-x1, y1, ida, pc, rs, bsthod);
	genorders(x+x2, y, irow-x2, y1, ida, pc, rs, bsthod);

	return 1;
    }

}


// Calculate a set of generic statistics of a time series
double* tscoeffs(double* ts, int bidx, int eidx, int ons)
{

    int i, ss, head, ind, cc;
    double* coeffs, *data;
    size_t* sts;
    double me, iva;

    iva=-0.3;
    ss=eidx-bidx;
    if (ss<1)
    {
	cout<<"Error is tscoeffs, eidx less than bidx."<<endl;
	return NULL;
    }

    coeffs=new double[ons];
    data=new double[ss];
    sts=new size_t[ss];
    for(i=bidx;i<eidx;i++)
    {
	data[i-bidx]=ts[i];
    }

    gsl_sort_index(sts, data, 1, ss);

    ind=sts[ss-1];
    if (data[ind]>iva)
    {
	coeffs[4]=(float)ind;  // timing of the maximum
	coeffs[5]=data[ind];   // the value of the maximum

	if (data[0]>iva && data[ss-1]>iva)  // The abs. difference of between the last and the first time series
	{
	    coeffs[6]=data[ss-1]-data[0];
	}
	else
	{
	    coeffs[6]=-999.0;
	}

	if (data[0]>0 && data[ss-1]>0 )  // The rate of change between the last and the first time series
	{
	    coeffs[7]=exp((log(data[ss-1]/data[0]))/(ss-1))-1;
	}
	else
	{
	    coeffs[7]=-999.0;
	}


	head=0;
	for(i=0;i<ss;i++)
	{
	    ind=sts[i];
	    if (data[ind]>iva)   
	    {
		//cout<<" ind="<<ind<<" ii="<<i<<" data[ind]="<<data[ind]<<" "<<(data[ind]-iva)<<" ";
		coeffs[2]=ind;  // timing of the minimum
		coeffs[3]=data[ind]; // Value of the minimum
		head=i;
		break;
	    }
	    else
	    {
		data[ind]=DBL_MAX;
	    }
	}
	if (head!=0)
	{
	    cc=ss-head;
	    gsl_sort(data,1,ss);
	}
	else
	{
	    cc=ss;
	}
	if (cc>1)
	{    
	    me = gsl_stats_mean(data, 1, cc); // Mean and variance of ts excluding the invalid data
	    coeffs[0]=me;
	    coeffs[1]=sqrt(gsl_stats_variance_m(data, 1, cc, me));
	}
	else
	{
	    coeffs[0]=coeffs[5];
	    coeffs[1]=0;
	}

    }
    else
    {
	for(i=0;i<ons;i++)
	{
	    coeffs[i]=-999.0;
	}
    }


    delete [] sts;
    delete [] data;
    return coeffs;
}


// Centre data on each dimension (row) of set X

int centre(gsl_matrix* X)
{

    int irow, icol, i, j;
    double sum, me, tvd;
    double* onerow;
    irow=X->size1;
    icol=X->size2;

    onerow=new double[icol];

    for(i=0;i<irow;i++)
    {	
	sum=0;
	for(j=0;j<icol;j++)
	{
	    sum+=gsl_matrix_get(X,i,j);
	}
	me=sum/icol;
	for(j=0;j<icol;j++)
	{
	    tvd=gsl_matrix_get(X,i,j)-me;
	    gsl_matrix_set(X,i,j,tvd);
	}
    }

    delete [] onerow;
}

int standardarray_f(float* data, int pnum, float ivd)
{

    int j, cc;

    float me, std;
    float* sdata;

    sdata=new float[pnum];

    cc=0;
    for(j=0;j<pnum;j++)
    {
	if (data[j]>ivd)
	{
	    sdata[cc] = data[j];
	    cc++;
	}
    }

    me=gsl_stats_float_mean(sdata, 1, cc);
    std=gsl_stats_float_sd_m(sdata, 1, cc, me);
    cout<<"me="<<me<<" std="<<std<<endl;

    for(j=0;j<pnum;j++)
    {
	if (data[j]>ivd)
	{
	    data[j]=(data[j]-me)/std;
	}
    }

    delete [] sdata;
    return 0;

}


int standardarray(double* data, int pnum, double ivd)
{

    int j, cc;

    double me, std;
    double* sdata;

    sdata=new double[pnum];

    cc=0;
    for(j=0;j<pnum;j++)
    {
	if (data[j]>ivd)
	{
	    sdata[cc] = data[j];
	    cc++;
	}
    }

    me=gsl_stats_mean(sdata, 1, cc);
    std=gsl_stats_sd_m(sdata, 1, cc, me);
    cout<<"me="<<me<<" std="<<std<<" cc="<<cc<<" pnum="<<pnum<<endl;

    for(j=0;j<pnum;j++)
    {
	if (data[j]>ivd)
	{
	    data[j]=(data[j]-me)/std;
	}
    }

    delete [] sdata;
    return 0;

}



// standarise data on each dimension (row) of set X
int standarise(gsl_matrix* X)
{

    int irow, icol, i, j;
    double sum, me, std, tvd;
    double* onerow;
    irow=X->size1;
    icol=X->size2;

    onerow=new double[icol];

    for(i=0;i<irow;i++)
    {	
	for(j=0;j<icol;j++)
	{
	    onerow[j]=gsl_matrix_get(X,i,j);
	}
	me=gsl_stats_mean(onerow, 1, icol);
	std=gsl_stats_sd_m(onerow, 1, icol, me);
	for(j=0;j<icol;j++)
	{
	    tvd=(gsl_matrix_get(X,i,j)-me)/std;
	    gsl_matrix_set(X,i,j,tvd);
	}
    }

    delete [] onerow;
}



// Principal component analysis on a set of data specified in X, 
// the data vectors are placed as column vectors in X so
// if each data has m features and there are total n data in the set, then
// X will be an m x n matrix, output the ordered m principal components as column vectors of the output matrix
// which will be and m x m matrix

gsl_matrix* pca(gsl_matrix* X)
{
    int i, irow, icol;
    gsl_matrix *Xd,  *cvm, *evec;
    gsl_vector *eval;
    gsl_eigen_symmv_workspace* w;

    irow=X->size1;
    icol=X->size2;

    centre(X);  // Centre data on each dimension (row) of set X
    Xd=gsl_matrix_alloc(irow, icol);
    evec=gsl_matrix_alloc(irow, irow);
    eval=gsl_vector_alloc(irow);

    w=gsl_eigen_symmv_alloc(irow);

    gsl_matrix_memcpy(Xd, X);
    cvm=covmatrix_col(Xd);
    gsl_eigen_symmv(cvm, eval, evec, w);

    gsl_eigen_symmv_sort(eval, evec, GSL_EIGEN_SORT_VAL_DESC);

    //gsl_blas_dgemm(CblasTrans, CblasNoTrans, 1, evec, X, 0, pa);

    gsl_eigen_symmv_free(w);
    gsl_matrix_free(cvm);
    gsl_matrix_free(Xd);
    gsl_vector_free(eval);

    return evec;
}

//  Return normalized eigenvalues and eigenvector of real symmetric matrix X
//  eigenvalues are sorted in descendent order and stored in vector eval
//  while the corresponding eigenvector are stored in the columns of the matrix evec
int basicpca(gsl_matrix* X, gsl_vector*& eval, gsl_matrix*& evec)
{
    int irow, icol;
    gsl_eigen_symmv_workspace* w;


    irow=X->size1;
    icol=X->size2;

    evec=gsl_matrix_alloc(irow, irow);
    eval=gsl_vector_alloc(irow);

    w=gsl_eigen_symmv_alloc(irow);

    gsl_eigen_symmv(X, eval, evec, w);

    gsl_eigen_symmv_sort(eval, evec, GSL_EIGEN_SORT_VAL_DESC);
    gsl_eigen_symmv_free(w);



    return 0;
}


// Calculate the covariance matrix of  a set of data, the data is specified by matrix X, 
// the data vectors are placed as column vectors in X so
// if each data has m features and there are total n data in the set, then
// X is an m x n matrix, output matrix will be an m x m symmetric matrix

gsl_matrix* covmatrix_col(gsl_matrix* X)
{
    int i, irow, icol;
    double* dptr;
    double me;
    gsl_matrix *Xt, *pa;
    gsl_vector *onerow;

    irow=X->size1;
    icol=X->size2;

    onerow=gsl_vector_alloc(icol);
    pa=gsl_matrix_calloc(irow, irow);
    Xt=gsl_matrix_alloc(icol, irow);

    for(i=0;i<irow;i++)
    {
	gsl_matrix_get_row(onerow, X, i);
	dptr=gsl_vector_ptr(onerow, 0);
	me=gsl_stats_mean(dptr, 1, icol);
	gsl_vector_add_constant(onerow, -me);
	gsl_matrix_set_row(X, i, onerow);
    }


    gsl_blas_dgemm(CblasNoTrans, CblasTrans, 1, X, X, 0, pa);
    gsl_vector_free(onerow);

    return pa;


}

// Calculate the covariance matrix of  a set of data, the data is specified by matrix X, 
// the data vectors are placed as row vectors in X so
// if each data has m features and there are total n data in the set, then
// X is an  n x m matrix, output matrix will be an m x m symmetric matrix


gsl_matrix* covmatrix_row(gsl_matrix* X)
{
    int irow, icol;
    gsl_matrix *pa, *Xt;

    irow=X->size1;
    icol=X->size2;

    Xt=gsl_matrix_alloc(icol, irow);
    gsl_matrix_transpose_memcpy(Xt, X);

    pa=covmatrix_col(Xt);
    gsl_matrix_free(Xt);

    return pa;
}


double guasmml(double* x, int N, double dta)
{

    double vr, half, nm, pi;

    half=0.5;
    nm=N-1.0;
    pi=3.1415926;

    if (N<5)
    {
	//cout<<"Number of data is too small...."<<endl;	
	return -1;
    }

    vr=gsl_stats_variance(x, 1, N);

    return half*nm*log(vr)+half*nm+half*N*log(2*pi/(dta*dta))+half*log(2*N*N);
}

bool remoutliners_gs(double** data, int ss, int ind, double dta, double ivd, double ivd2)
{
    int i, cc, pd, N, j, head, pp, cp;
    double minmsg,  msg, Rmax, me, vr, std, th1, th2;
    double *x, *r;
    size_t* sts, *cdx, *ndx;


    x=new double[ss];
    r=new double[ss];
    sts=new size_t[ss];
    cdx=new size_t[ss];
    ndx=new size_t[ss];

    cc=0;
    gsl_sort_index(sts, data[ind], 1, ss);
    for(i=0;i<ss;i++)
    {
	pd=sts[i];
	if (data[ind][pd]>ivd)
	{
	    x[cc]=data[ind][pd];
	    cc++;
	}
    }

    N=cc;
    head=ss-cc;

    if (N<20)
    {
	delete [] x;
	delete [] r;
	delete [] sts;
	delete [] cdx;
	delete [] ndx;

	return false;
    }

    cp=0;
    msg=gsl_stats_variance(x, 1, N);
    for(i=1;i<N/5;i++)
    {
	vr=gsl_stats_variance(x, 1, N-i);
	if (msg/vr>1.1)
	{
	    cp=i;
	    break;
	}
	msg=vr;
    }

    /*
       minmsg=guasmml(x, N, dta);
       cp=0;
    //    cout<<"N="<<N<<" minmsg="<<minmsg<<" rate="<<minmsg/N<<endl;
    for(i=1;i<N/5;i++)
    {
    msg=guasmml(x, N-i, dta);
    me=gsl_stats_mean(x, 1, N-i);
    vr=gsl_stats_variance_m(x, 1, N-i, me);
    //Rmax=10000-(me+1.97*sqrt(vr));
    Rmax=10000-x[N-i-1];
    //	cout<<"i="<<i<<" ";
    //	cout<<msg<<" rate1="<<msg/(N-i)<<" range="<<Rmax<<" mean="<<me<<" std="<<sqrt(vr)<<" rate2="<<log(Rmax/dta);
    msg+=i*log(Rmax/dta);
    if (msg<minmsg && msg>0)
    {
    minmsg=msg;
    cp=i;
    }
    //	cout<<" msg=";
    //	cout<<msg<<endl;
    }
    // cout<<endl;
     */

    cp=10;
    me=gsl_stats_mean(x, 1, N-cp);
    vr=gsl_stats_variance_m(x, 1, N-cp, me);
    std=sqrt(vr);

    if (cp>0)
    {
	cc=0;
	//cout<<"ind="<<ind<<" cp="<<cp<<" *** ";
	for(i=10;i>=1;i--)
	{
	    //cout<<x[N-i];
	    if ((x[N-i]-me)/std>2.1)
	    {
		//cout<<"* ";
		cdx[cc]=sts[head+N-i];
		cc++;
	    }
	    else
	    {
		// cout<<"  ";
	    }
	}
	//cout<<endl;

	pp=0;
	//cout<<"low value spike, ind="<<ind<<" cp="<<cp<<" *** ";
	for(i=0;i<10;i++)
	{
	    // cout<<x[i];
	    if ((x[i]-me)/std<-2.1)
	    {
		//cout<<"* ";
		ndx[pp]=sts[head+i];
		pp++;
	    }
	    else
	    {
		//cout<<"  ";
	    }
	}
	//cout<<endl;

	r[0]=DBL_MAX;
	for(i=1;i<ss;i++)
	{
	    if (data[ind][i]>0 && data[ind][i-1]>0)
	    {
		//r[i]=log(data[ind][i]/data[ind][i-1]);
		r[i]=data[ind][i]-data[ind][i-1];
	    }
	    else if (data[ind][i]>ivd && data[ind][i-1]>ivd)
	    {
		//r[i]=log((data[ind][i]-ivd)/(data[ind][i-1]-ivd));
		r[i]=data[ind][i] - data[ind][i-1];
	    }
	    else
	    {
		r[i]=DBL_MAX;
	    }
	}

	gsl_sort_index(sts, r, 1, ss);
	for(j=0;j<ss/2;j++)
	{
	    if (r[sts[ss-j-1]]!=DBL_MAX)
	    {
		break;
	    }
	}
	j=ss-j;
	int a1, a2;

	a1=(int)(j*0.05);
	a2=(int)(j*0.95);
	a1=(int)sts[a1];
	a2=(int)sts[a2];
	th1=r[a1];
	th2=r[a2];

	//cout<<"th1="<<th1<<" th2="<<th2<<endl;
	//cout<<"Found outliners: ";
	for(i=0;i<cc;i++)
	{
	    pd=cdx[i];
	    if (r[pd]>th2)
	    {    
		if (pd<ss-1)
		{
		    if (r[pd+1]<th1)
		    {
			//cout<<data[ind][pd-1]<<" ";
			//cout<<data[ind][pd]<<" ";
			//cout<<data[ind][pd+1]<<" "<<endl;
			data[ind][pd]=ivd2;
		    }
		}
	    }
	}
	//cout<<endl;

	//cout<<"Found low value outliners: ";
	for(i=0;i<pp;i++)
	{
	    pd=ndx[i];
	    if (r[pd]<th1)
	    {    
		if (pd<ss-1)
		{
		    if (r[pd+1]>th2)
		    {
			//cout<<data[ind][pd-1]<<" ";
			//cout<<data[ind][pd]<<" ";
			//cout<<data[ind][pd+1]<<" "<<endl;
			data[ind][pd]=ivd2;
		    }
		}
	    }
	}
	//cout<<endl;

    }
    delete [] x;
    delete [] r;
    delete [] sts;
    delete [] cdx;
    delete [] ndx;
    return true;
}
bool remoutliners(double** data, int ss, int ind, double dta)
{
    int i, cc, pd, N, j, head, pp, cp;
    double ivd, ivd2, minmsg,  msg, Rmax, me, vr, std, th1, th2;
    double *x, *r;
    size_t* sts, *cdx, *ndx;


    ivd=-3000.0;
    ivd2=-4000.0;
    x=new double[ss];
    r=new double[ss];
    sts=new size_t[ss];
    cdx=new size_t[ss];
    ndx=new size_t[ss];

    cc=0;
    gsl_sort_index(sts, data[ind], 1, ss);
    for(i=0;i<ss;i++)
    {
	pd=sts[i];
	if (data[ind][pd]>ivd)
	{
	    x[cc]=data[ind][pd];
	    cc++;
	}
    }

    N=cc;
    head=ss-cc;

    if (N<20)
    {
	delete [] x;
	delete [] r;
	delete [] sts;
	delete [] cdx;
	delete [] ndx;

	return false;
    }

    cp=0;
    msg=gsl_stats_variance(x, 1, N);
    for(i=1;i<N/5;i++)
    {
	vr=gsl_stats_variance(x, 1, N-i);
	if (msg/vr>1.1)
	{
	    cp=i;
	    break;
	}
	msg=vr;
    }

    /*
       minmsg=guasmml(x, N, dta);
       cp=0;
    //    cout<<"N="<<N<<" minmsg="<<minmsg<<" rate="<<minmsg/N<<endl;
    for(i=1;i<N/5;i++)
    {
    msg=guasmml(x, N-i, dta);
    me=gsl_stats_mean(x, 1, N-i);
    vr=gsl_stats_variance_m(x, 1, N-i, me);
    //Rmax=10000-(me+1.97*sqrt(vr));
    Rmax=10000-x[N-i-1];
    //	cout<<"i="<<i<<" ";
    //	cout<<msg<<" rate1="<<msg/(N-i)<<" range="<<Rmax<<" mean="<<me<<" std="<<sqrt(vr)<<" rate2="<<log(Rmax/dta);
    msg+=i*log(Rmax/dta);
    if (msg<minmsg && msg>0)
    {
    minmsg=msg;
    cp=i;
    }
    //	cout<<" msg=";
    //	cout<<msg<<endl;
    }
    // cout<<endl;
     */

    cp=10;
    me=gsl_stats_mean(x, 1, N-cp);
    vr=gsl_stats_variance_m(x, 1, N-cp, me);
    std=sqrt(vr);

    if (cp>0)
    {
	cc=0;
	//cout<<"ind="<<ind<<" cp="<<cp<<" *** ";
	for(i=10;i>=1;i--)
	{
	    //cout<<x[N-i];
	    if ((x[N-i]-me)/std>2.1)
	    {
		//cout<<"* ";
		cdx[cc]=sts[head+N-i];
		cc++;
	    }
	    else
	    {
		// cout<<"  ";
	    }
	}
	//cout<<endl;

	pp=0;
	//cout<<"low value spike, ind="<<ind<<" cp="<<cp<<" *** ";
	for(i=0;i<10;i++)
	{
	    // cout<<x[i];
	    if ((x[i]-me)/std<-2.1)
	    {
		//cout<<"* ";
		ndx[pp]=sts[head+i];
		pp++;
	    }
	    else
	    {
		//cout<<"  ";
	    }
	}
	//cout<<endl;

	r[0]=DBL_MAX;
	for(i=1;i<ss;i++)
	{
	    if (data[ind][i]>0 && data[ind][i-1]>0)
	    {
		//r[i]=log(data[ind][i]/data[ind][i-1]);
		r[i]=data[ind][i]-data[ind][i-1];
	    }
	    else if (data[ind][i]>ivd && data[ind][i-1]>ivd)
	    {
		//r[i]=log((data[ind][i]-ivd)/(data[ind][i-1]-ivd));
		r[i]=data[ind][i] - data[ind][i-1];
	    }
	    else
	    {
		r[i]=DBL_MAX;
	    }
	}

	gsl_sort_index(sts, r, 1, ss);
	for(j=0;j<ss/2;j++)
	{
	    if (r[sts[ss-j-1]]!=DBL_MAX)
	    {
		break;
	    }
	}
	j=ss-j;
	int a1, a2;

	a1=(int)(j*0.05);
	a2=(int)(j*0.95);
	a1=(int)sts[a1];
	a2=(int)sts[a2];
	th1=r[a1];
	th2=r[a2];

	//cout<<"th1="<<th1<<" th2="<<th2<<endl;
	//cout<<"Found outliners: ";
	for(i=0;i<cc;i++)
	{
	    pd=cdx[i];
	    if (r[pd]>th2)
	    {    
		if (pd<ss-1)
		{
		    if (r[pd+1]<th1)
		    {
			//cout<<data[ind][pd-1]<<" ";
			//cout<<data[ind][pd]<<" ";
			//cout<<data[ind][pd+1]<<" "<<endl;
			data[ind][pd]=ivd2;
		    }
		}
	    }
	}
	//cout<<endl;

	//cout<<"Found low value outliners: ";
	for(i=0;i<pp;i++)
	{
	    pd=ndx[i];
	    if (r[pd]<th1)
	    {    
		if (pd<ss-1)
		{
		    if (r[pd+1]>th2)
		    {
			//cout<<data[ind][pd-1]<<" ";
			//cout<<data[ind][pd]<<" ";
			//cout<<data[ind][pd+1]<<" "<<endl;
			data[ind][pd]=ivd2;
		    }
		}
	    }
	}
	//cout<<endl;

    }
    delete [] x;
    delete [] r;
    delete [] sts;
    delete [] cdx;
    delete [] ndx;
    return true;
}

int spatialfilter(double** data, double* lme, int band, int icol, int rowmin, int rowmax, int colmin, int colmax,
	int x, int y, int width, double thod)
{
    int i, j, offs, px, py, ss, ivd, idx, ind, err;
    double* a, *b, *r;
    double me, sigma, xyme;
    size_t* sts;

    if (width%2!=1)
    {
	cout<<"The size of the windows must be an odd number."<<endl;
	return -1;
    }
    ivd=-3000;

    if (data[x*icol+y][band]<=ivd)
    {

	return -2;
    }


    offs=(width-1)/2;

    a=new double[width*width];
    r=new double[width*width];
    sts=new size_t[width*width];

    px=x-offs; // row index number of the top left corner
    py=y-offs; // row index number of the top left corner

    if (px<rowmin)
    {
	px=rowmin;
    }

    if (py<colmin)
    {
	py=colmin;
    }

    if (px+width>=rowmax)
    {
	px=rowmax-width+1;
    }

    if (py+width>=colmax)
    {
	py=colmax-width+1;
    }

    ss=0;
    for(i=px;i<px+width;i++)
    {
	for(j=py;j<py+width;j++)
	{
	    ind=i*icol+j;
	    if (data[ind][band]>ivd)
	    {
		a[ss]=data[ind][band];
		if (i==x && j==y)
		{
		    idx=ss;
		}
		ss++;
	    }
	}
    }

    if (ss>3)
    {
	me=gsl_stats_mean(a, 1, ss); 
	sigma=sqrt(gsl_stats_variance_m(a, 1, ss, me));
    }
    else // too many bad samples
    {

	delete [] a;
	delete [] r;
	delete [] sts;
	return -3;
    }

    xyme=lme[x*icol+y];
    ss=0;
    err=0;
    for(i=px;i<px+width;i++)
    {
	for(j=py;j<py+width;j++)
	{
	    ind=i*icol+j;
	    if (data[ind][band]>ivd)
	    {
		if (fabs(lme[ind]-xyme)<sigma/3)
		{
		    a[ss]=data[ind][band];
		    if (i==x && j==y)
		    {
			idx=ss;
		    }
		    ss++;
		}
	    }
	    else
	    {
		err++;
	    }
	}
    }

    if (err>width*width*.75)
    {
	//cout<<"Found point among noisy samples."<<endl;
	data[x*icol+y][band]=-4000;
	delete [] a;
	delete [] r;
	delete [] sts;
	return 0;
    }

    if (ss>3)
    {
	me=gsl_stats_mean(a, 1, ss); 
	sigma=sqrt(gsl_stats_variance_m(a, 1, ss, me));
    }
    else // too few samples
    {
	/*
	   if (a[idx]>6000 || a[idx]<1000)
	   {
	   cout<<"lme[ind]="<<lme[ind]<<" band="<<band+1;
	   cout<<" sample="<<y+1<<" line="<<x+1<<" val="<<a[idx]<<" mean="<<me<<" sigma="<<sigma<<" ss="<<ss<<endl;

	   }
	 */

	delete [] a;
	delete [] r;
	delete [] sts;
	return -4;
    }



    for(i=0;i<ss;i++)
    {
	r[i]=(a[i]-me)/sigma;
	/*
	   cout<<r[i];
	   if (i!=idx)
	   {
	   cout<<"  ";
	   }
	   else
	   {
	   cout<<"* ";
	   }
	 */
    }
    /*
       gsl_sort_index(sts, r, 1, ss);
       for(i=0;i<ss;i++)
       {
       if (sts[i]==idx)
       {
       break;
       }
       }
     */
    // cout<<endl;
    if (r[idx]>thod || r[idx]<=-thod)
    {    
	//cout<<"found , r[idx]="<<r[idx]<<" position="<<i<<" band="<<band+1;
	//cout<<" sample="<<y+1<<" line="<<x+1<<" val="<<a[idx]<<" mean="<<me<<" sigma="<<sigma<<" ss="<<ss<<endl;
	data[x*icol+y][band]=-4000;
    }

    delete [] a;
    delete [] r;
    delete [] sts;
    return 0;
}



int findtails(double ** data, int ind, int bands, double ivd, int*& tails, int& nt, double rt, int dr)
{

    int i, ss, pp, cc;
    size_t* sts;

    sts=new size_t[bands];

    gsl_sort_index(sts, data[ind], 1, bands);
    ss=(int)floor(bands*rt);
    if (dr==0 || dr==1)
    {
	tails=new int[ss];
    }
    else
    {
	tails=new int[2*ss];
    }

    i=0;
    nt=0;
    cc=0;
    if (dr==0 || dr==2)  // Find  bands*rt instance with lowest 
    {
	for(i=0;i<bands;i++)
	{
	    pp=sts[i];
	    if (data[ind][pp]>ivd)
	    {
		tails[cc]=pp;
		cc++;
	    }
	    if (cc==ss)
	    {
		break;
	    }
	}
	nt=cc;
    }
    cc=0;
    if (dr==1 || dr==2) // Find highest band
    {
	for(i=bands-1;i>=0;i--)
	{
	    pp=sts[i];
	    if (data[ind][pp]>ivd)
	    {
		tails[nt+cc]=pp;
		cc++;
	    }
	    if (cc==ss)
	    {
		break;
	    }
	}
	nt=nt+cc;
    }

    delete [] sts;
    // delete [] tails;

}

double* advtscoeffs(double* ts, int bands, int bidx, int eidx, int minp, int maxp,  int ans, int tpres)
{
    int i, ons, t, x, j, cc, pp, ss, f1, f2, ind, years, amaxcc, amincc;
    double* coeffs, *wcoef, *advs, *oneyear, *peaktm, *anlow;
    double** fds;
    double ivd, dta, baseline, vthod, sum, amax, topline, mincyc, amin;
    size_t* sts;
    int* hits;
    bool flag;


    advs=new double[ans];
    ivd=-0.3;
    cc=0;
    for(i=bidx;i<eidx;i++)
    {
	if (ts[i]>ivd)
	{
	    cc++;
	}
    }

    if (cc<23)
    {
	for(i=0;i<ans;i++)
	{
	    advs[i]=-999;
	}
	return advs;	
    }


    ons=8;
    dta=0.001;

    creatematrix(fds, ons+2, (eidx-bidx)*(maxp-minp+1));
    for(i=0;i<ans;i++)
    {
	advs[i]=0;
    }

    cc=0;
    years=(eidx-bidx)/tpres;

    wcoef=tscoeffs(ts, bidx, eidx, ons);
    advs[0]=wcoef[0];
    advs[1]=wcoef[1];

    // cout<<advs[0]<<" "<<advs[1]<<" *** "<<endl;

    for (t=minp;t<maxp;t++)
    {
	for(x=bidx;x<eidx-t;x++)
	{
	    // cout<<"x="<<x<<" ts[x]="<<ts[x]<<"  ts[x+t-1]="<<ts[x+t-1]<<" x+t="<<x+t<<endl;
	    if (ts[x]>ivd && ts[x+t-1]>ivd)
	    {
		coeffs=tscoeffs(ts, x, x+t,  ons);
		for(i=0;i<ons;i++)
		{
		    fds[i][cc]=coeffs[i];
		}
		fds[ons][cc]=x;
		fds[ons+1][cc]=t;
		cc++;
		delete [] coeffs;
	    }
	}
    }
    ss=cc;

    if (ss<years*3)
    {
	for(i=0;i<ans;i++)
	{
	    advs[i]=-999;
	}
	delete [] wcoef;
	deletematrix(fds, ons+2);
	return advs;	
    }

    // to find the flatness rate

    sts=new size_t[(eidx-bidx)*(maxp-minp+1)];
    hits=new int[bands];
    oneyear=new double[bands];
    peaktm=new double[bands];
    anlow=new double[bands];

    //cout<<"before find baseline, ss="<<ss<<endl;
    baseline=findbaseline(ts, bands, ivd,  dta);
    gsl_sort_index(sts, fds[ons+1], 1, ss);
    vthod=wcoef[1]/2;

    for(i=bidx;i<eidx;i++)
    {
	hits[i]=0;
    }

    for(i=ss-1;i>=0;i--)
    {
	ind=sts[i];
	if (fds[0][ind]<baseline && fds[1][ind]<vthod)
	    //if (fds[0][ind]<baseline )
	{
	    f1=(int)fds[ons][ind];
	    f2=(int)(fds[ons+1][ind]+fds[ons][ind]);

	    for(j=f1;j<f2;j++)
	    {
		hits[j]=1;
	    }
	}
    }



    cc=0;
    for(i=bidx;i<eidx;i++)
    {
	if (hits[i]>0)
	{
	    cc++;
	}
    }

    advs[2]=((double) cc)/(eidx-bidx);

    /*
       if (cc==0)
       {
       cout<<"baseline="<<baseline<<" vthod="<<vthod<<endl;
       }
     */


    // to find the rate of drop
    gsl_sort_index(sts, fds[ons-1], 1, ss);  // Sort according to rate of change
    for(i=bidx;i<eidx;i++)
    {
	hits[i]=0;
    }
    cc=0;
    i=0;
    sum=0;
    do 
    {
	ind=sts[i];
	if (fds[ons-1][ind]>-999)
	{
	    f1=(int)fds[ons][ind];
	    f2=(int)(fds[ons+1][ind]+fds[ons][ind]);
	    flag=true;
	    for(j=f1;j<f2;j++)
	    {
		if (hits[j]==1)
		{
		    flag=false;
		    break;
		}
	    }
	    if (flag)
	    {
		for(j=f1;j<f2;j++)
		{
		    hits[j]=1;
		}
		sum+=fds[ons-1][ind];
		cc++;
	    }
	}
	i++;
    }while(cc<years && i<ss);
    advs[4]=sum/cc;

    // to find the rate of rise
    for(i=bidx;i<eidx;i++)
    {
	hits[i]=0;
    }

    cc=0;
    i=ss-1;
    sum=0;

    do 
    {
	ind=sts[i];
	f1=(int)fds[ons][ind];
	f2=(int)(fds[ons+1][ind]+fds[ons][ind]);
	flag=true;
	for(j=f1;j<f2;j++)
	{
	    if (hits[j]==1)
	    {
		flag=false;
		break;
	    }
	}
	if (flag)
	{
	    for(j=f1;j<f2;j++)
	    {
		hits[j]=1;
	    }
	    sum+=fds[ons-1][ind];
	    cc++;
	}
	i--;
    }while(cc<years && i>=0);
    advs[3]=sum/cc;

    gsl_sort_index(sts, ts, 1, bands);  // Sort according to time series values
    cc=0;
    sum=0;
    for(i=0;i<bands;i++)
    {
	ind=sts[i];
	if (ts[ind]>ivd && ind>=bidx && ind<eidx)
	{
	    sum+=ts[ind];
	    cc++;
	}
	if (cc==years)
	{
	    break;
	}
    }
    if (cc>0)
    {
	advs[5]=sum/cc;
    }
    else
    {
	advs[5]=-999;
    }



    amax=0;
    amaxcc=0;
    amin=0;
    amincc=0;
    for(i=0;i<years;i++)
    {

	f1=bidx+i*tpres;
	f2=bidx+(i+1)*tpres;
	cc=0;
	for(j=f1;j<f2;j++)
	{
	    oneyear[cc]=ts[j];
	    cc++;
	}
	//cout<<"i="<<i<<" cc="<<cc<<" f1="<<f1<<" f2="<<f2<<endl;
	gsl_sort_index(sts, oneyear, 1, cc);
	ind=sts[cc-1];
	if (oneyear[ind]>ivd)
	{
	    amax+=oneyear[ind];
	    peaktm[amaxcc]=(double) ind;
	    amaxcc++;
	    /*
	       for(j=0;j<cc;j++)
	       {
	       ind=sts[j];
	       if (oneyear[ind]>ivd)
	       {
	       amin+=oneyear[ind];
	       amincc++;
	       break;
	       }
	       }
	     */
	}
	for(j=0;j<cc;j++)
	{
	    ind=sts[j];
	    if (oneyear[ind]<=ivd)
	    {
		continue;
	    }
	    if (j<cc-1)
	    {
		anlow[amincc]=oneyear[ind];
		amincc++;
		j++;
		ind=sts[j];
		anlow[amincc]=oneyear[ind];
		amincc++;
		break;
	    }
	}

    }

    sum=0;
    if (amincc>0)
    {
	for(j=0;j<amincc;j++)
	{
	    sum+=anlow[j];
	}
	if (amincc>6)
	{
	    gsl_sort(anlow,1,amincc);
	    sum-=anlow[0];
	    sum-=anlow[1];
	    advs[11]=sum/(amincc-2);
	}
	else
	{
	    advs[11]=sum/amincc;
	}
    }
    else
    {
	advs[11]=-999;
    }

    /*
       if (advs[5]!=-999 && amincc>0)
       {
       amin/=amincc;
       advs[6]=amin/advs[5];
       }
       else
       {
       advs[6]=-999;
       }
     */

    if (amaxcc>0)
    {

	gsl_sort_index(sts, ts, 1, bands);  // Sort according to time series values
	cc=0;
	sum=0;
	for(i=bands-1;i>=0;i--)
	{
	    ind=sts[i];
	    if (ts[ind]>ivd && ind>=bidx && ind<eidx)
	    {
		sum+=ts[ind];
		cc++;
	    }
	    if (cc==amaxcc)
	    {
		break;
	    }
	}

	if (cc>0)
	{
	    advs[7]=sum/cc;
	}
	else
	{
	    advs[7]=-999;
	}

	if (advs[7]!=-999 && amaxcc>0)
	{
	    amax/=amaxcc;
	    advs[8]=amax/advs[7];
	    if (advs[8]>1)
	    {
		cout<<"amax="<<amax<<" amaxcc="<<amaxcc<<" gmax="<<advs[7]<<endl;
	    }
	}
	else
	{
	    advs[8]=-999;
	}
    }
    else
    {
	advs[7]=-999;
	advs[8]=-999;
    }


    if (amaxcc>3)
    {
	advs[9]=gsl_stats_mean(peaktm, 1, amaxcc);
	advs[10]=sqrt(gsl_stats_variance_m(peaktm, 1, amaxcc, advs[9]));
    }
    else
    {
	advs[9]=-999;
	advs[10]=-999;
    }

    gsl_sort_index(sts, fds[9], 1, ss);  // Sort according to length of a cycle

    for(i=bidx;i<eidx;i++)
    {
	hits[i]=0;
    }

    sum=0;
    cc=0;
    topline=advs[0]+advs[1];
    mincyc=5;
    for(i=0;i<ss;i++)
    {
	ind=sts[i];
	f1=(int)fds[ons][ind];
	f2=(int)(fds[ons+1][ind]+fds[ons][ind]);

	if (fds[5][ind]>topline && ts[f1]<baseline && ts[f2-1]<baseline && ts[f1]>ivd && ts[f2-1]>ivd && fds[9][ind]>mincyc)		
	{
	    flag=true;
	    for(j=f1;j<f2;j++)
	    {
		if (hits[j]==1)
		{
		    flag=false;
		    break;
		}
	    }
	    if (flag)
	    {
		for(j=f1;j<f2;j++)
		{
		    hits[j]=1;
		}
		sum+=fds[9][ind];
		cc++;
	    }
	}
    }

    if (cc>0)
    {
	advs[6]=sum/cc-1;
    }
    else
    {
	advs[6]=0;
    }

    // 0    bandnames.push_back("Mean");
    // 1    bandnames.push_back("Standard deviation");
    // 2    bandnames.push_back("Flatness");
    // 3    bandnames.push_back("Rate of rise");
    // 4    bandnames.push_back("Rate of drop");
    // 5    bandnames.push_back("Global minimum");
    // 6    bandnames.push_back("Avg. length of a cycle");
    // 7    bandnames.push_back("Global maximum");
    // 8    bandnames.push_back("Annual max / Global max");
    // 9    bandnames.push_back("Mean of timing of the maximum");
    // 10   bandnames.push_back("Sd of timing of the maximum");


    //    for(i=0;i<5;i++) 
    //    {
    //	cout<<advs[i]<<" ";
    //    }



    delete [] wcoef;
    delete [] hits;
    delete [] peaktm;
    delete [] oneyear;
    delete [] anlow;
    delete [] sts;
    deletematrix(fds, ons+2);
    return advs;	
}


double findbaseline(double* ts, int bands, double ivd, double dta)
{
    int i, cc, ind, ss, lk, lp, minsh, bestlk;
    size_t* sts;
    double *ksp, *psp; 
    double baseline, minmsg, msg, sigma;

    if (bands<16)
    {
	return -1000;
    }


    sts=new size_t[bands];
    gsl_sort_index(sts, ts, 1, bands);
    cc=0;
    for(i=0;i<bands;i++)
    {
	ind=sts[i];
	if (ts[ind]>ivd)
	{
	    break;
	}
	else
	{
	    cc++;
	} 
    }

    ss=bands-cc;

    if (ss<16)
    {
	delete [] sts;
	return -2000;
    }


    ksp=new double[bands];
    psp=new double[bands];

    minsh=5;

    for(i=0;i<ss-minsh;i++)
    {
	ind=sts[i+cc];
	ksp[i]=ts[ind];
    }
    for(i=ss-minsh;i<ss;i++)
    {
	ind=sts[i+cc];
	psp[i-ss+minsh]=ts[ind];
    }

    lk=ss-minsh;
    lp=minsh;
    minmsg=DBL_MAX;
    do
    {
	//msg=guasmml(ksp , lk, dta)+ guasmml(psp ,lp, dta);
	msg=gsl_stats_variance(ksp , 1, lk)*lk+ gsl_stats_variance(psp ,1, lp)*lp;
	if (msg<minmsg)
	{
	    minmsg=msg;
	    baseline=gsl_stats_mean(ksp, 1, lk);
	    sigma=sqrt(gsl_stats_variance_m(ksp, 1, lk, baseline));
	    bestlk=lk;
	}
	//cout<<"lp="<<lp<<" lk="<<lk<<" msg="<<msg<<" minmsg="<<minmsg<<endl;
	psp[lp]=ksp[lk-1];
	lp++;
	lk--;
    }while(lk>=minsh);

    /*
       cout<<"baselineme="<<baseline<<" sigma="<<sigma<<" lk="<<bestlk<<" ss="<<ss<<endl;
       for(i=0;i<bestlk;i++)
       {
       cout<<ksp[i]<<" ";
       }
       cout<<endl;
     */

    delete [] sts;    	
    delete [] ksp;    	
    delete [] psp;  

    return baseline-0.618*sigma;
    //return baseline;
}

// Generate a kernel matrix from data matrix X
// X -- the set of input data, where each column of X represents an instance of the data
// centred -- if it is true, calculated the centred version of the kernel, otherwise just calculate using original data
// kt -- the type of kernel function
// np -- the number of parameters of the kernel function
// pa -- the list of the parameters

gsl_matrix* findakernel(gsl_matrix* X, bool centred, int kt, double* pa, double& sum, double*& colsum)
{

    int i, j, irow, icol;
    double kij, val;
    gsl_matrix *K, *KP;
    //    gsl_vector_view vi, vj;
    gsl_vector* pvi, *pvj;

    irow=X->size1;
    icol=X->size2;

    K=gsl_matrix_alloc(icol, icol);

#pragma omp parallel private(i, j, pvi, pvj, kij) firstprivate(kt, icol, pa)
#pragma omp for schedule(dynamic,20) nowait
    for(i=0;i<icol;i++)
    {
	pvi=&(gsl_matrix_column(X,i).vector);
	for(j=i;j<icol;j++)
	{
	    pvj=&(gsl_matrix_column(X,j).vector);
	    kij=calkernel(pvi,pvj,kt,pa);
	    //cout<<"i="<<i<<" j="<<j<<" kij="<<kij<<endl;
	    gsl_matrix_set(K,i,j,kij);
	    gsl_matrix_set(K,j,i,kij);
	}
    }
    if (centred)
    {
	colsum=new double[icol];
	sum=0;
	for(i=0;i<icol;i++)
	{
	    colsum[i]=0;
	    for(j=0;j<icol;j++)
	    {
		colsum[i]+=gsl_matrix_get(K, i, j);
	    }
	    sum+=colsum[i];
	    colsum[i]/=icol;
	}
	sum/=(icol*icol);
	KP=gsl_matrix_alloc(icol, icol);
	for(i=0;i<icol;i++)
	{
	    for(j=i;j<icol;j++)
	    {
		val=gsl_matrix_get(K, i, j)-(colsum[i]+colsum[j])+sum;
		gsl_matrix_set(KP, i, j, val);
		gsl_matrix_set(KP, j, i, val);
	    }
	}
	gsl_matrix_free(K);
	return KP;
    }
    else
    {
	return K;
    }
}


// calculate the value of kernel function specified by kt and pa of input vector v1 and v2
double calkernel(gsl_vector* v1, gsl_vector* v2, int kt, double* pa)
{
    double r, norm, d, c;
    int len, i;
    gsl_vector* v3;

    // showvector(v1);
    // showvector(v2);
    if (kt==1)  // RBF kernel
    {
	r=pa[0];
	len=v1->size;
	v3=gsl_vector_alloc(len);

	gsl_vector_memcpy(v3, v1);
	gsl_vector_sub(v3,v2);
	gsl_blas_ddot(v3,v3,&norm);
	gsl_vector_free(v3);
	//	cout<<"norm="<<norm<<" r="<<r<<" kerl="<<exp(-norm*r)<<endl;
	return exp(-norm*r);
    }
    else if (kt==2) // d-order polynomial kernel
    {
	d=pa[0];
	c=pa[1];
	gsl_blas_ddot(v1,v2,&norm);
	return pow(norm+c,d);
    }
}

int kernelpca(gsl_matrix* X, int kt, double* pa, gsl_vector*& eval, gsl_matrix*& evec, int& p, double& sum, double*& colsum)
{

    gsl_matrix* K; 
    bool centred;

    centred=true;

    K=findakernel(X, centred, kt, pa, sum, colsum);
    basicpca(K, eval, evec);
    p=fspacenormalised(eval, evec);

    gsl_matrix_free(K);
    return 0;
}

int fspacenormalised( gsl_vector* eval, gsl_matrix* evec)
{
    int i, icol;
    double r, a1, a2;
    gsl_vector_view vv;
    gsl_vector* ptrv;

    icol=evec->size2;

    for(i=0;i<icol;i++)
    {
	//cout<<"i="<<i<<" "<<endl;
	a2=gsl_vector_get(eval,i);
	if (a2>0 && !isnan(a2))
	{
	    vv=gsl_matrix_column(evec, i);
	    ptrv=&vv.vector;
	    a1=gsl_blas_dnrm2(ptrv);
	    r=1/(a1*sqrt(a2));
	    gsl_vector_scale(ptrv,r);
	    //a1=a2*gsl_blas_dnrm2(ptrv)*gsl_blas_dnrm2(ptrv);
	    //cout<<"a1="<<a1<<" a2="<<a2<<endl;
	}
	else
	{
	    break;
	}
    }
    return i;
}

// Return the first p kernel PC of vector x given 
double* kpcacoeffs(gsl_matrix* X, int kt, double* pa, gsl_vector* x, gsl_matrix* evec, double sum, double* colsum, int p)
{
    int i, j, M;
    double* kpca, *xxk;
    double a, val;

    gsl_vector_view vv;
    gsl_vector* ptrv;

    M=evec->size2;

    kpca=new double[p];
    xxk=new double[M];
    val=0;
    for(i=0;i<M;i++)
    {
	vv=gsl_matrix_column(X, i); // Get X_k
	ptrv=&vv.vector;
	xxk[i]=calkernel(x, ptrv, kt, pa);
	val+=xxk[i];
    }

    val/=M;
    for(i=0;i<M;i++)
    {
	xxk[i]=xxk[i]-val-colsum[i]+sum;
    }


    for(i=0;i<p;i++)
    {
	kpca[i]=0;
	vv=gsl_matrix_column(evec, i); // Get a_i
	ptrv=&vv.vector;
	for(j=0;j<M;j++)
	{
	    a=gsl_vector_get(ptrv, j);
	    val=a*xxk[j];
	    kpca[i]+=val;
	}
    }

    delete [] xxk;
    return kpca;
}

int SVclustering_wf(gsl_matrix* XX,  double v,  int kt, double* pa, int& nc, int*& xcls, double ivd)
{
    gsl_matrix *K, *X;
    gsl_vector_view aview;
    gsl_rng* rng;

    double sum, maxph, ph, rvm, eta, rsq, oldsum, esma, fy;
    double* colsum, *a, *fw;
    size_t* sts;
    bool* vidx;
    int* cls;

    int i, j, ind, natb, m, cc, found, ty, prg, p, k,sam, svcc, stallcc, maxstall, ps, ss;

    rng=gsl_rng_alloc(gsl_rng_taus);
    gsl_rng_set(rng, time(NULL));



    ss=XX->size2;
    natb=XX->size1;
    vidx=new bool[ss];
    cc=ss;
    for(i=0;i<ss;i++)
    {
	vidx[i]=true;
	for(j=0;j<natb;j++)
	{
	    if (gsl_matrix_get(XX, j, i)<=ivd)
	    {
		vidx[i]=false;
		cc--;
		break;
	    }
	}
    }

    m=cc; 

    cls=NULL;
    if (m<50)
    {

	delete [] vidx;
	cout<<"Too few training samples (<50) ... "<<endl;
	return -1;
    }

    if (m>20000)
    {
	delete [] vidx;
	cout<<"Too many training samples (>20000) ... "<<endl;
	return -2;
    }

    if (v>=1)
    {
	delete [] vidx;
	cout<<"v must be less than one"<<endl;
	return -3;
    }

    xcls=new int[ss];
    X=gsl_matrix_alloc(natb, m);
    cc=0;
    cout<<"m="<<m<<endl;
    for(i=0;i<ss;i++)
    {
	if (vidx[i])
	{
	    for(j=0;j<natb;j++)
	    {
		fy=gsl_matrix_get(XX,j,i);
		gsl_matrix_set(X, j, cc, fy);
	    }
	    cc++;
	}
    }

    //  for(i=0;i<ss;i++)
    //  {
    //	for(j=0;j<natb;j++)
    //	{
    //	    cout<<gsl_matrix_get(X, j, i)<<" ";
    //	}
    //	cout<<endl;
    //    }

    K=findakernel(X, false, kt, pa, sum, colsum);

    // Initialise coefficients array a
    a=new double[m];
    fw=new double[m];
    sts=new size_t[m];
    cls=new int[m];
    rvm=1.0/(v*m);

    randomsimplex(rng, a, m);

    gsl_sort_index(sts, a, 1, m);
    cc=0;
    sum=0;
    for(i=0;i<m;i++)
    {
	j=sts[m-i-1];
	if (a[j]>rvm)
	{
	    for(k=cc;k<m;k++)
	    {
		p=sts[k];
		if (a[p]+a[j]<2*rvm)
		{
		    a[p]=a[p]+a[j]-rvm;
		    a[j]=rvm;
		    cc=k+1;
		    break;
		}
	    }
	}
	else
	{
	    break;
	}
    }


    maxph=-1;
    aview=gsl_vector_view_array(a, m);
    for(i=0;i<m;i++)
    {
	ph=hyperdistance(K, &aview.vector, i);
	if (ph>maxph && a[i]>0)
	{
	    maxph=ph;
	}
	fw[i]=ph;
    }

    ph=maxph;
    esma=0.0000001;
    stallcc=0;
    maxstall=300;
    //maxstall=180;
    while(1)
    {
	ty=1;
	// find a pair of coefficients to be updated 
	//found=scan_kkt(rng, ty, m, fw, a, ph, rvm, i, j);
	found=scan_kkt_v2(rng, ty, m, fw, a, ph, rvm, i, j);
	//	cout<<"ty="<<ty<<" i="<<i<<" a[i]="<<a[i]<<" fw[i]="<<fw[i];
	//	cout<<" j="<<j<<" a[j]="<<a[j]<<" fw[j]="<<fw[j]<<" ph="<<ph;
	//	cout<<" found="<<found<<endl;
	if (found)
	{
	    prg=updatecoeffs(K, a, fw, i, j, rvm, ph);
	    //	    cout<<"ty="<<ty<<" rvm="<<rvm<<" i="<<i<<" a[i]="<<a[i]<<" fw[i]="<<fw[i];
	    //	    cout<<" j="<<j<<" a[j]="<<a[j]<<" fw[j]="<<fw[j]<<" ph="<<ph<<endl<<endl;
	    ty=2;
	    oldsum=0;
	    for(k=0;k<m;k++)
	    {
		for(p=0;p<m;p++)
		{
		    oldsum+=a[p]*a[k]*gsl_matrix_get(K, k, p);
		}
	    }
	    while(1)
	    {
		//found=scan_kkt(rng, ty, m, fw, a, ph, rvm, i, j);
		found=scan_kkt_v2(rng, ty, m, fw, a, ph, rvm, i, j);
		//cout<<"ty="<<ty<<" rvm="<<rvm<<" i="<<i<<" a[i]="<<a[i]<<" fw[i]="<<fw[i];
		//cout<<" j="<<j<<" a[j]="<<a[j]<<" fw[j]="<<fw[j]<<" ph="<<ph<<" "<<ph;
		//cout<<" found="<<found<<endl;
		if (found)
		{
		    prg=updatecoeffs(K, a, fw, i, j, rvm, ph);
		    //cout<<"prg="<<prg<<" ty="<<ty<<" i="<<i<<" a[i]="<<a[i]<<" fw[i]="<<fw[i];
		    //cout<<" j="<<j<<" a[j]="<<a[j]<<" fw[j]="<<fw[j]<<" ph="<<ph<<" "<<stallcc<<endl<<endl;

		}
		else
		{
		    break;
		}
	    }
	}
	else
	{
	    break;
	}
	sum=0;
	svcc=0;
	cc=0;
	for(k=0;k<m;k++)
	{
	    if (a[k]>0 && a[k]<rvm)
	    {
		svcc++;
	    }
	    if (a[k]>0 && a[k]<0.0001)
	    {
		cc++;
	    }
	    for(p=0;p<m;p++)
	    {
		sum+=a[p]*a[k]*gsl_matrix_get(K, k, p);
	    }
	}
	cout<<fabs(sum-oldsum)/sum<<" svcc="<<svcc<<" ph="<<ph<<" sum="<<sum<<" stallcc="<<stallcc<<" cc="<<cc<<endl<<endl;
	//	if (fabs(sum-oldsum)/sum<esma || sum>oldsum)
	//	{
	stallcc++;
	//	}
	if (stallcc>maxstall)
	{
	    break;
	}
    }

    sum=0;
    for(k=0;k<m;k++)
    {
	for(p=0;p<m;p++)
	{
	    sum+=a[p]*a[k]*gsl_matrix_get(K, k, p);
	}
    }


    for(i=0;i<m;i++)
    {
	if (a[i]>0.0001 && a[i]<rvm-0.0001)
	    //if (a[i]>0 && a[i]<rvm)
	{
	    rsq=gsl_matrix_get(K,i,i)-2*fw[i]+sum;
	    break;
	}
    }



    sam=30;
    ps=30;



    // Create clusters according to coefficients array a
    //  createcluster_v1(X, a, rng, sam, kt, pa, rsq, sum, rvm, nc, cls);
    //  mergeclusters( rng,  cls, ps, sam,  a,  X, kt,  pa, rsq, sum,  nc);
    //  adjustcluster(cls, nc, K);

    // Create clusters according to coefficients array a
    createcluster_v2(X, K, a, sam, kt, pa, rsq, sum, rvm, nc, cls);

    //    relables(cls,  m, v, nc);

    cc=0; 
    for(i=0;i<ss;i++)
    {
	if (vidx[i])
	{
	    xcls[i]=cls[cc];
	    cc++;
	}
	else
	{
	    xcls[i]=(int)ivd;
	}
    }

    //   for(i=0;i<ss;i++)
    //   {
    //	for(j=0;j<natb;j++)
    //	{
    //	    cout<<gsl_matrix_get(XX, j, i)<<" ";
    //	}
    //	cout<<xcls[i]<<endl;
    //  }

    gsl_matrix_free(K);
    gsl_matrix_free(X);


    delete [] vidx;
    delete [] cls;
    delete [] a;
    delete [] fw;
    delete [] sts;
    gsl_rng_free(rng);
    return 0;

}

// Support vector clustering
int SVclustering(gsl_matrix* X,  double v,  int kt, double* pa, int& nc, int* cls, svminfo* svf)
{
    gsl_matrix *K;
    gsl_vector_view aview;
    gsl_rng* rng;

    double sum, maxph, ph, rvm, eta, rsq, oldsum, esma, fy;
    double* colsum, *a, *fw;
    size_t* sts;

    int i, j, ind, natb, m, cc, found, ty, prg, p, k,sam, svcc, stallcc, maxstall, ps, ss;

    rng=gsl_rng_alloc(gsl_rng_taus);
    gsl_rng_set(rng, time(NULL));

    m=X->size2;
    natb=X->size1;


    //cls=NULL;
    if (m<50)
    {

	cout<<"Too few training samples (<50) ... "<<endl;
	return -1;
    }

    if (m>20000)
    {
	cout<<"Too many training samples (>20000) ... "<<endl;
	return -2;
    }

    if (v>=1)
    {
	cout<<"v must be less than one"<<endl;
	return -3;
    }

    //   cls=new int[m];
    //   X=gsl_matrix_alloc(natb, m);

    //  for(i=0;i<ss;i++)
    //  {
    //	for(j=0;j<natb;j++)
    //	{
    //	    cout<<gsl_matrix_get(X, j, i)<<" ";
    //	}
    //	cout<<endl;
    //    }

    K=findakernel(X, false, kt, pa, sum, colsum);

    // Initialise coefficients array a
    a=new double[m];
    fw=new double[m];
    sts=new size_t[m];
    rvm=1.0/(v*m);

    randomsimplex(rng, a, m);

    gsl_sort_index(sts, a, 1, m);
    cc=0;
    sum=0;
    for(i=0;i<m;i++)
    {
	j=sts[m-i-1];
	if (a[j]>rvm)
	{
	    for(k=cc;k<m;k++)
	    {
		p=sts[k];
		if (a[p]+a[j]<2*rvm)
		{
		    a[p]=a[p]+a[j]-rvm;
		    a[j]=rvm;
		    cc=k+1;
		    break;
		}
	    }
	}
	else
	{
	    break;
	}
    }


    maxph=-1;
    aview=gsl_vector_view_array(a, m);
    for(i=0;i<m;i++)
    {
	ph=hyperdistance(K, &aview.vector, i);
	if (ph>maxph && a[i]>0)
	{
	    maxph=ph;
	}
	fw[i]=ph;
    }

    ph=maxph;
    esma=0.0000001;
    stallcc=0;
    //maxstall=300;
    maxstall=180;
    while(1)
    {
	ty=1;
	// find a pair of coefficients to be updated 
	//found=scan_kkt(rng, ty, m, fw, a, ph, rvm, i, j);
	found=scan_kkt_v2(rng, ty, m, fw, a, ph, rvm, i, j);
	//	cout<<"ty="<<ty<<" i="<<i<<" a[i]="<<a[i]<<" fw[i]="<<fw[i];
	//	cout<<" j="<<j<<" a[j]="<<a[j]<<" fw[j]="<<fw[j]<<" ph="<<ph;
	//	cout<<" found="<<found<<endl;
	if (found)
	{
	    prg=updatecoeffs(K, a, fw, i, j, rvm, ph);
	    //	    cout<<"ty="<<ty<<" rvm="<<rvm<<" i="<<i<<" a[i]="<<a[i]<<" fw[i]="<<fw[i];
	    //	    cout<<" j="<<j<<" a[j]="<<a[j]<<" fw[j]="<<fw[j]<<" ph="<<ph<<endl<<endl;
	    ty=2;
	    oldsum=0;
	    for(k=0;k<m;k++)
	    {
		for(p=0;p<m;p++)
		{
		    oldsum+=a[p]*a[k]*gsl_matrix_get(K, k, p);
		}
	    }
	    while(1)
	    {
		//found=scan_kkt(rng, ty, m, fw, a, ph, rvm, i, j);
		found=scan_kkt_v2(rng, ty, m, fw, a, ph, rvm, i, j);
		//cout<<"ty="<<ty<<" rvm="<<rvm<<" i="<<i<<" a[i]="<<a[i]<<" fw[i]="<<fw[i];
		//cout<<" j="<<j<<" a[j]="<<a[j]<<" fw[j]="<<fw[j]<<" ph="<<ph<<" "<<ph;
		//cout<<" found="<<found<<endl;
		if (found)
		{
		    prg=updatecoeffs(K, a, fw, i, j, rvm, ph);
		    //cout<<"prg="<<prg<<" ty="<<ty<<" i="<<i<<" a[i]="<<a[i]<<" fw[i]="<<fw[i];
		    //cout<<" j="<<j<<" a[j]="<<a[j]<<" fw[j]="<<fw[j]<<" ph="<<ph<<" "<<stallcc<<endl<<endl;

		}
		else
		{
		    break;
		}
	    }
	}
	else
	{
	    break;
	}
	sum=0;
	svcc=0;
	cc=0;
	for(k=0;k<m;k++)
	{
	    if (a[k]>0 && a[k]<rvm)
	    {
		svcc++;
	    }
	    if (a[k]>0 && a[k]<0.0001)
	    {
		cc++;
	    }
	    for(p=0;p<m;p++)
	    {
		sum+=a[p]*a[k]*gsl_matrix_get(K, k, p);
	    }
	}
	//cout<<fabs(sum-oldsum)/sum<<" svcc="<<svcc<<" ph="<<ph<<" sum="<<sum<<" stallcc="<<stallcc<<" cc="<<cc<<endl<<endl;
	//	if (fabs(sum-oldsum)/sum<esma || sum>oldsum)
	//	{
	cout<<stallcc<<" ";
	stallcc++;
	//	}
	if (stallcc>maxstall)
	{
	    cout<<endl;
	    break;
	}
    }

    sum=0;
    for(k=0;k<m;k++)
    {
	for(p=0;p<m;p++)
	{
	    sum+=a[p]*a[k]*gsl_matrix_get(K, k, p);
	}
    }


    for(i=0;i<m;i++)
    {
	if (a[i]>0.0001 && a[i]<rvm-0.0001)
	    //if (a[i]>0 && a[i]<rvm)
	{
	    rsq=gsl_matrix_get(K,i,i)-2*fw[i]+sum;
	    break;
	}
    }



    sam=30;
    ps=30;

    for(i=0;i<m;i++)
    {
	svf->a[i]=a[i];
    }

    svf->rsq=rsq;
    svf->sum=sum;
    // Create clusters according to coefficients array a
    //  createcluster_v1(X, a, rng, sam, kt, pa, rsq, sum, rvm, nc, cls);
    //  mergeclusters( rng,  cls, ps, sam,  a,  X, kt,  pa, rsq, sum,  nc);
    //  adjustcluster(cls, nc, K);

    // Create clusters according to coefficients array a


    createcluster_v3(X, K,  sam, kt, pa, rvm, nc, cls, svf);
    // Counting the class
    //
    //
    int* cnm;
    cnm=new int[nc];
    for(i=0;i<nc;i++)
    {
	cnm[i]=0;
    }

    for(i=0;i<m;i++)
    {
	ind=cls[i];
	cnm[ind]++;
    }
    for(i=0;i<nc;i++)
    {
	cout<<"Cluster #"<<i<<" consists of "<<cnm[i]<<" pixels"<<endl;
    }
    delete [] cnm;



    gsl_matrix_free(K);


    delete [] a;
    delete [] fw;
    delete [] sts;
    gsl_rng_free(rng);
    return 0;

}

// Trend analysis for MODIS time series
double* trendcoeffs(double* data, int bands, int bx1,  int years, int sam, int ans, int tpres)
{

    double* advs, *ts, *mits, *mets, *mats, *x;
    double ivd, sum, c0, c1, cov00, cov01, cov11, sumsq, res;

    int i, j, cc, micc, mecc, macc, pos;

    advs=new double[ans];
    for(i=0;i<ans;i++)
    {
	advs[i]=-999;
    }
    if (bx1+years*tpres>bands)
    {
	cout<<"Not enough data points...."<<endl;
	return advs;
    }


    ts=new double[tpres];
    mits=new double[sam*years];
    mets=new double[sam*years];
    mats=new double[sam*years];
    ivd=-0.3;
    cc=0;

    micc=0;
    mecc=0;
    macc=0;
    for(i=0;i<years;i++)
    {
	pos=i*tpres+bx1;
	sum=0;
	cc=0;
	for(j=0;j<tpres;j++)
	{
	    ts[j]=data[pos+j];
	    if (ts[j]>ivd)
	    {
		sum+=ts[j];
		cc++;
	    }
	}
	gsl_sort(ts,1,tpres);
	if (ts[tpres-1]<=ivd || cc<3)  // There is no valid data in this year, continue to next year
	{
	    delete [] ts;
	    delete [] mits;
	    delete [] mets;
	    delete [] mats;
	    return advs;
	}
	mets[mecc]=sum/cc;
	mecc++;
	cc=0;
	j=0;
	do
	{
	    if (ts[cc]>ivd)
	    {
		mits[micc]=ts[cc];
		micc++;
		j++;
	    }	
	    cc++;
	}while(j<sam && cc<tpres);

	if (j<sam)
	{
	    delete [] ts;
	    delete [] mits;
	    delete [] mets;
	    delete [] mats;
	    return advs;
	}

	cc=tpres-1;
	j=0;
	do
	{
	    if (ts[cc]>ivd)
	    {
		mats[macc]=ts[cc];
		macc++;
		j++;
	    }	
	    cc--;
	}while(j<sam && cc>=0);

	if (j<sam)
	{
	    delete [] ts;
	    delete [] mits;
	    delete [] mets;
	    delete [] mats;
	    return advs;
	}

    }

    if (mecc!=years || micc!=sam*years || macc!=sam*years)
    {
	delete [] ts;
	delete [] mits;
	delete [] mets;
	delete [] mats;
	return advs;
    }

    x=new double[sam*years];

    for(i=0;i<years;i++)
    {
	x[i]=(double)i;
    }

    gsl_fit_linear(x, 1, mets, 1, years, &c0, &c1, &cov00, &cov01, &cov11, &sumsq);
    advs[3]=c1;
    advs[4]=mets[0];
    advs[5]=mets[years-1];



    cc=0;
    res=1.0/tpres;
    for(i=0;i<years;i++)
    {
	for(j=0;j<sam;j++)
	{
	    x[cc]=i+res*j;
	    cc++;
	}
    }

    gsl_fit_linear(x, 1, mits, 1, sam*years, &c0, &c1, &cov00, &cov01, &cov11, &sumsq);
    advs[0]=c1;
    advs[1]=0;
    advs[2]=0;
    for(j=0;j<sam;j++)
    {
	advs[1]+=mits[j];
	advs[2]+=mits[sam*years-1-j];
    }
    advs[1]/=sam;
    advs[2]/=sam;

    gsl_fit_linear(x, 1, mats, 1, sam*years, &c0, &c1, &cov00, &cov01, &cov11, &sumsq);
    advs[6]=c1;
    advs[7]=0;
    advs[8]=0;
    for(j=0;j<sam;j++)
    {
	advs[7]+=mats[j];
	advs[8]+=mats[sam*years-1-j];
    }
    advs[7]/=sam;
    advs[8]/=sam;

    delete [] x;
    delete [] ts;
    delete [] mits;
    delete [] mets;
    delete [] mats;
    return advs;
}


double	hyperdistance(gsl_matrix* K, gsl_vector* a, int ind)
{

    gsl_vector* pvj;
    double dd;

    pvj=&gsl_matrix_column(K, ind).vector;

    gsl_blas_ddot(pvj, a, &dd);

    return dd;
}

// Find the data point which maximises the gain for SMO algorithm
int findsmoj(int i, int m, double* a, double* fw, double rvm, double esma)
{

    int k, j;
    double* phdf;
    double maxdf;

    phdf=new double[m];

    maxdf=esma;
    for(k=0;k<m;k++)
    {
	phdf[k]=0;
    }

#pragma omp parallel private(k) firstprivate(i, m, rvm)
#pragma omp for schedule(dynamic, 100) nowait
    for(k=0;k<m;k++)
    {
	//if ( fabs(ph-fw[k])>esma && a[k]>0 && a[k]<rvm) 
	if ( a[k]>0 && a[k]<rvm) 
	{
	    if (a[i]==0)
	    {
		phdf[k]=fw[k]-fw[i];
	    }
	    else if (a[i]==rvm)
	    {
		phdf[k]=fw[i]-fw[k];
	    }
	    else
	    {
		phdf[k]=fabs(fw[i]-fw[k]);
	    }

	}
    }

    j=gsl_stats_max_index(phdf, 1, m);

    if (phdf[j]<maxdf)
    {
	j=-1;	
    }


    delete [] phdf;

    return j;
}

// find a pair of coefficients to be updated 
int scan_kkt_v2(gsl_rng* rng, int ty, int m, double* fw, double* a, double ph, double rvm, int& i, int& j)
{
    int p, k, h, cc1, cc2, pi, ss, pj, gd, found;
    double maxdf, esma;
    bool flag;

    size_t* sts;
    int* list1, *list2;
    double* phdf;

    list1=new int[m];
    list2=new int[m];

    flag=false;
    esma=0.0000001;
    //  esma*=100;
    //  esma*=0.01;
    maxdf=esma;
    cc2=0;
    for(k=0;k<m;k++)
    {

	if ( fabs(ph-fw[k])>esma && a[k]>0 && a[k]<rvm)
	    //if (ph!=fw[k] && a[k]>0 && a[k]<rvm)
	{
	    list2[cc2]=k;
	    cc2++;
	}    
    }
    for(k=0;k<cc2;k++)
    {
	list1[k]=list2[k];
    }

    cc1=cc2;
    if (ty==1)
    {
	for(k=0;k<m;k++)
	{
	    if ((a[k]==0 && fw[k]<ph) || (a[k]>rvm && fw[k]> ph ))
	    {
		list1[cc1]=k;
		cc1++;
	    }
	}
    }

    if (cc2==0)
    {
	if (cc1>1)
	{
	    for(k=0;k<cc1;k++)
	    {
		list2[k]=list1[k];
	    }
	    cc2=cc1;
	}
	else
	{
	    delete [] list1;
	    delete [] list2;
	    return 0;
	}
    }

    //cout<<"cc1="<<cc1<<" cc2="<<cc2<<" m="<<m<<endl;

    ss=cc1*cc2;
    phdf=new double[ss];


#pragma omp parallel private(k, pi, pj, p) firstprivate(list1, list2, fw, phdf, cc1, cc2)
#pragma omp for schedule(dynamic ) nowait
    for(k=0;k<cc1;k++)
    {
	pi=list1[k];
	for(p=0;p<cc2;p++)
	{
	    pj=list2[p];
	    phdf[k*cc2+p]=fabs(fw[pi]-fw[pj]);
	}
    }


    //   cout<<" ss="<<ss<<endl;
    gd=gsl_stats_max_index(phdf, 1, ss);
    k=(int)(floor(gd/cc2));
    p=gd%cc2;

    //   cout<<" p="<<p<<" k="<<k<<" gd="<<gd<<endl;
    i=list1[k];
    j=list2[p];

    //   cout<<" i="<<i<<" j="<<j<<" phdf[gd]="<<phdf[gd]<<" maxdf="<<maxdf<<endl;
    //    cout<<"here"<<endl;
    if (phdf[gd]>maxdf)
    {
	found=1;
    }
    else
    {
	found=0;
    }

    delete [] list1;
    delete [] list2;
    delete [] phdf;

    return found;
}

// find a pair of coefficients to be updated 
int scan_kkt(gsl_rng* rng, int ty, int m, double* fw, double* a, double ph, double rvm, int& i, int& j)
{
    int p, k, h;
    double maxdf, phdf, esma;
    bool flag;

    size_t* sts;

    sts=randomperm(rng, m);

    flag=false;
    esma=0.0000001;
    esma*=0.01;
    maxdf=esma;
    if (ty==1)
    {
	for(h=0;h<m;h++)
	{
	    p=sts[h];
	    //if ((fw[p]-ph)*a[p]>0 || (fabs(ph-fw[p])>esma && a[p]>0 && a[p]<rvm)|| (a[p]==0 && fw[p]<ph) ) // KKT condition
	    if ((fw[p]-ph)*a[p]>0 || (ph!=fw[p] && a[p]>0 && a[p]<rvm)|| (a[p]==0 && fw[p]<ph) ) // KKT condition
	    {
		i=p;
		j=findsmoj(i, m, a, fw, rvm, esma);
		if (j!=-1)
		{
		    flag=true;
		    break;
		}
	    }
	}
    }
    else
    {
	for(h=0;h<m;h++)
	{
	    p=sts[h];
	    //if ( fabs(ph-fw[p])>esma && a[p]>0 && a[p]<rvm) 
	    if ( ph!=fw[p] && a[p]>0 && a[p]<rvm) 
	    {
		i=p;
		j=findsmoj(i, m, a, fw, rvm, esma);
		if (j!=-1)
		{
		    flag=true;
		    break;
		}
	    }
	}

    }

    //    cout<<"i="<<i<<" j="<<j<<endl;
    delete [] sts;
    if (flag)
    {
	return 1;
    }
    else
    {
	return 0;
    }

}

int randomsimplex(gsl_rng* rng, double* a, int m)
{
    int i, j, n;
    double* b;

    if (m<2)
    {
	return -1;
    }

    n=m-1;
    b=new double[n];

    for(i=0;i<n;i++)
    {
	b[i]=gsl_rng_uniform(rng);	    
    }
    gsl_sort(b,1,n);
    a[0]=b[0];
    for(i=1;i<n;i++)
    {
	a[i]=b[i]-b[i-1];
    }
    a[m-1]=1.0-b[n-1];

    delete [] b;
}

// Generate a random permutation of m
size_t* randomperm(gsl_rng* rng, int m)
{
    size_t* sts;
    double* a;
    int i;

    if (m<2)
    {
	return NULL;
    }

    sts=new size_t[m];
    a=new double[m];


    for(i=0;i<m;i++)
    {
	a[i]=gsl_rng_uniform(rng);	    
    }

    gsl_sort_index(sts, a, 1, m);

    delete [] a;
    return sts;

}

// Generate a random permutation of n out of m instances
size_t* randomperm(gsl_rng* rng, int m, int n)
{
    size_t* sts;
    double* a;
    int i;

    if (m<2)
    {
	return NULL;
    }

    sts=new size_t[n];
    a=new double[m];


    for(i=0;i<m;i++)
    {
	a[i]=gsl_rng_uniform(rng);	    
    }

    gsl_sort_smallest_index(sts, n, a, 1, m);

    delete [] a;
    return sts;

}

// Generate a random permutation of n out of m instances, excluding invalid data, assuming n<<m
size_t* randomperm(gsl_rng* rng, int m, double ssr, int& n, float* data, double ivd)
{
    size_t* sts, *idx, *perm;
    bool* a;
    int i, cc, px, pp, ind;
    double r;

    if (m<2)
    {
	return NULL;
    }

    a=new bool[m];

    cc=0;
    for(i=0;i<m;i++)
    {
	if (data[i]>ivd)
	{
	    a[i]=false;
	    cc++;
	}
	else
	{
	    a[i]=true;
	}
    }
    if (cc==0)
    {
	delete [] a;
	return NULL;
    }


    n= (int) (ssr*cc);
    sts=new size_t[n];

    cout<<"In randomperm #of valid points="<<cc<<" The target sub set will consist of "<<n<<" pixels"<<endl;

    if (cc<20000000)
    {
	idx=new size_t[cc];
	pp=0;
	for(i=0;i<m;i++)
	{
	    if (!a[i])
	    {
		idx[pp]=i;
		pp++;
	    }
	}

	perm =  randomperm(rng, cc);
	for(i=0;i<n;i++)
	{
	    ind=perm[i];
	    sts[i]=idx[ind];
	}

	delete [] idx;
	delete [] perm;
    }
    else
    {
	cc=0;
	while(true)
	{
	    r=gsl_rng_uniform(rng);	    
	    px=(size_t) (r*m);
	    if (!a[px])
	    {
		a[px]=true;
		sts[cc]=px;
		cc++;
		if (cc==n)
		{
		    break;
		}
	    }
	}
    }

    delete [] a;
    return sts;

}


// update a pair of coefficients
int updatecoeffs(gsl_matrix* K, double* a, double* fw, int i, int j, double rvm, double& ph)
{
    double gama, xx, L, H, kii, kij, kjj, ci, cj, ahi, ahj, sum , kki, kkj, nph;

    int m, k, ccV, ccB, ccZ, p;

    m=K->size1;

    gama =a[i]+a[j];
    kii=gsl_matrix_get(K, i, i);
    kjj=gsl_matrix_get(K, j, j);
    kij=gsl_matrix_get(K, i, j);

    xx=kii+kjj-2*kij;

    ci=fw[i]-a[i]*kii-a[j]*kij;
    cj=fw[j]-a[j]*kjj-a[i]*kij;

    L=gama-rvm;
    if (L<0)
    {
	L=0;
    }

    if (rvm<gama)
    {
	H=rvm;
    }
    else
    {
	H=gama;
    }

    //ahi=a[i]+(cj-ci+kjj*a[j]+kij*(a[j]-a[i])-kii*a[i])/xx;
    ahi=a[i]+(fw[j]-fw[i])/xx;
    if (ahi<L)
    {
	ahi=L;
    }
    if (ahi>H)
    {
	ahi=H;
    }
    //cout<<cj-ci+kjj*a[j]+kij*(a[j]-a[i])-kii*a[i]<<endl;

    // cout<<"ahi-a[i]="<<ahi-a[i]<<" gamma="<<gama<<" L="<<L<<" H="<<H<<" fw[j]-fw[i]="<<fw[j]-fw[i]<<" xx="<<xx<<endl;
    /*
       ccB=0;
       ccZ=0;
       ccV=0;
       sum=0;
       for(k=0;k<m;k++)
       {
       if (a[k]>0 && a[k]<rvm)
       {
       ccV++;
       }
       else if (a[k]==0)
       {
       ccZ++;
       }
       else if (a[k]==rvm)
       {
       ccB++;
       }
       sum+=a[k];
       }
       cout<<" # of BSV ="<<ccB<<" ";
       cout<<" # of SV ="<<ccV<<" ";
       cout<<" # of NSV ="<<ccZ<<" ";
       cout<<" # of total ="<<ccZ+ccV+ccB<<" sum="<<sum<<endl;
     */
    if (a[i]==ahi)
    {
	return 0;
    }
    ahj=gama-ahi;	


#pragma omp parallel private(k, kki, kkj, sum) firstprivate(m, ahi, ahj, i, j, fw, a)
#pragma omp for schedule(dynamic ) nowait
    for(k=0;k<m;k++)
    {
	kki=gsl_matrix_get(K,k,i);
	kkj=gsl_matrix_get(K,k,j);
	sum=a[i]*kki+ a[j]*kkj;
	fw[k]-=sum;
	sum=ahi*kki+ahj*kkj;
	fw[k]+=sum;
    }

    a[i]=ahi;
    a[j]=ahj;

    /*
    //  ph=-1;
    ccB=0;
    ccZ=0;
    ccV=0;
    sum=0;
    // ph=-1;
    for(k=0;k<m;k++)
    {
    if (a[k]>0 && a[k]<rvm)
    {
    ccV++;
    }
    else if (a[k]==0)
    {
    ccZ++;
    }
    else if (a[k]==rvm)
    {
    ccB++;
    }
    }

    for(k=0;k<m;k++)
    {
    for(p=0;p<m;p++)
    {
    sum+=a[p]*a[k]*gsl_matrix_get(K, k, p);
    }
    }
     */
    //    cout<<" # of BSV ="<<ccB<<" ";
    //    cout<<" # of SV ="<<ccV<<" ";
    //    cout<<" # of NSV ="<<ccZ<<" ";
    //    cout<<" # of total ="<<ccZ+ccV+ccB<<" sum="<<sum<<endl;


    if (a[i]>0 && a[i]<rvm)
    {
	if (a[j]>0 && a[j]<rvm)
	{
	    ph=(fw[i]+fw[j])/2;
	}
	else
	{
	    ph=fw[i];
	}
    }
    else
    {
	ph=fw[j];
    }


    return 1;
}

// Check weather vector pi and pj belong to the same cluster by sampling ss points between pi and pj
bool adjcheck(gsl_matrix* X, int i, int j, int ss, double* a, int kt, double* pa, double rsq, double sum)
{
    bool adj;
    gsl_vector* pi, *pj;
    pi=&gsl_matrix_column(X, i).vector;
    pj=&gsl_matrix_column(X, j).vector;

    adj=adjcheck2v(pi, pj, a, kt, pa, sum, rsq, ss, X);
    return adj;
}

bool adjcheck2v(gsl_vector* pi, gsl_vector* pj, double* a, int kt, double* pa, double sum, double rsq, int ss, gsl_matrix* X)
{
    bool adj;
    int k, m;
    double alp, beta, dd;

    gsl_vector *px; 

    m=pi->size;
    px=gsl_vector_alloc(m);
    adj=true;

    for(k=0;k<ss;k++)
    {
	gsl_vector_set_zero(px);
	alp=(k+1.0)/(ss+1.0);    	
	beta=1.0-alp;
	gsl_blas_daxpy(alp, pi, px);   // px=alp*pi;
	gsl_blas_daxpy(beta, pj, px);   // px=px+beta*pj, so px=alp*pi+beta*pj;
	dd=calrsq(px, a, X, kt, pa, sum);
	if (dd>rsq)
	{
	    adj=false;
	    break;
	}
    }

    gsl_vector_free(px);
    return adj;
}


double calrsq(gsl_vector* px, double* a, gsl_matrix* X, int kt, double* pa, double sum)
{
    int i, m;
    double rsq, wd;
    gsl_vector* pi;

    m=X->size2;
    rsq=calkernel(px, px, kt, pa)+sum;

    wd=0;
    for(i=0;i<m;i++)
    {
	pi=&gsl_matrix_column(X, i).vector;
	wd+=a[i]*calkernel(px, pi, kt, pa);	
    }
    wd*=2.0;
    rsq-=wd;
    return rsq;
}

int inducecluster_oned(bool* adj, bool* chk, int i, double* a, int m, int& nc, int* cls, double rvm)
{
    int j, pp, ind; 

    int* index;

    index=new int[m];
    pp=0;
    index[pp]=i;
    pp++;
    for(j=0;j<m;j++)
    {
	if (!chk[j])
	{
	    if (adj[j] && a[j]<rvm)
	    {
		index[pp]=j;
		pp++;
		chk[j]=true;
	    }
	}
    }

    for(j=0;j<pp;j++)
    {
	ind=index[j];
	cls[ind]=nc;
    }
    nc++;
}

// find all the point connect to point h directly or indirectly
int findgroup(int h, int m, bool** adj, int& pp, int* cdex, bool* chk)
{
    int i;

    chk[h]=true;
    for(i=0;i<m;i++)
    {
	if (adj[h][i] && !chk[i] )
	{
	    cdex[pp]=i;
	    pp++;
	    findgroup(i, m, adj, pp, cdex, chk);
	}    
    }
    return 0;
}

// Generate clusters from adjacency matrix adj
int clusterfromgraph(bool** adj, int m, int& nc, int*& cls)
{

    int i, j, pp, ind;
    bool* chk;
    int* cdex;


    cdex=new int[m];
    cls=new int[m];
    chk=new bool[m];


    for(i=0;i<m;i++)
    {
	chk[i]=false;
    }

    nc=1;
    // cout<<"m="<<m<<endl;

    for(i=0;i<m-1;i++)
    {
	if (!chk[i])
	{
	    cdex[0]=i;
	    pp=1;
	    //cout<<" before findgroup, i="<<i<<endl;
	    findgroup(i, m, adj, pp, cdex, chk);
	    for(j=0;j<pp;j++)
	    {
		ind=cdex[j];
		cls[ind]=nc;
		chk[ind]=true;
		//cout<<ind<<" ";
	    }
	    //cout<<"nc="<<nc<<endl;
	    nc++;
	}
    }
    if (!chk[m-1])
    {
	cls[m-1]=nc;
	nc++;
    }

    for(i=0;i<m;i++)
    {
	cout<<cls[i]<<" ";
    }
    cout<<endl;
    delete [] chk;
    delete [] cdex;


}

// Label the data according to the adjacency matrix adj
//
int inducecluster(bool** adj, double* a, int m, int& nc, int* cls, double rvm)
{
    bool* chk;
    int* index;
    int i, j, ind, cc, pp;

    chk=new bool[m];
    index=new int[m];
    cc=1;

    for(i=0;i<m;i++)
    {
	chk[i]=false;
    }

    do
    {
	if (!chk[i])
	{
	    if (a[i]==rvm)  // BSV, flag as outliners
	    {
		cls[i]=0;
	    }
	    else
	    {
		pp=0;
		index[pp]=i;
		pp++;
		chk[i]=true;
		for(j=i+1;j<m;j++)
		{
		    if (!chk[j])
		    {
			if (adj[i][j] && a[j]<rvm)
			{
			    index[pp]=j;
			    pp++;
			    chk[j]=true;
			}
		    }
		}
		for(j=0;j<pp;j++)
		{
		    ind=index[j];
		    cls[ind]=cc;
		}
		cc++;
	    }
	}
	i++;
    }while (i<m);
    delete [] chk;
    delete [] index;

}

int inducecluster_sv2(int svcc, int* svind, bool** adj, gsl_matrix* X, int sam, double* a, int kt, double* pa, double rsq, 
	double sum,  int& nc, int* cls)
{


    int i, j, ind, mc, m;
    double dd, mindd;
    int *svcls;
    bool flag;

    m=X->size2;

    nc=1;

    clusterfromgraph(adj, svcc, nc, svcls);
    for(i=0;i<svcc;i++)
    {
	ind=svind[i];
	cls[ind]=svcls[i];
    }

#pragma omp parallel private(i, j) firstprivate(X, m, svcc, sum, rsq, pa, kt, a, sam, svind)
#pragma omp for schedule(dynamic) nowait

    for(i=0;i<m;i++)
    {
	if (cls[i]<0)
	{
	    cls[i]=0;
	    for(j=0;j<svcc;j++)
	    {
		flag=adjcheck(X,  i,  svind[j],  sam,  a, kt,  pa, rsq, sum);
		if (flag)
		{
		    cls[i]=svcls[j];
		    break;
		}
	    }
	    if (j==svcc)
	    {
		cout<<"Label can not be found for the pixel"<<endl;
	    }
	}
    }

    // House keeping, eliminate (assign class label 0) to the clusters whose size are less than thd
    //consolidate(cls, m, (int)(m*.005), nc);
    consolidate(cls, m, (int)(m*.01), nc);
    delete [] svcls;
}

int inducecluster_sv3(int svcc, int* svind, bool** adj, gsl_matrix* X, int sam,  int kt, double* pa,  int& nc, int* cls, svminfo* svf)
{


    int i, j, ind, mc, m;
    double dd, mindd;
    int *svcls;
    bool flag;
    double* a;
    double rsq;
    double sum;

    a=svf->a;
    rsq=svf->rsq;
    sum=svf->sum;

    m=X->size2;

    nc=1;

    clusterfromgraph(adj, svcc, nc, svcls);
    for(i=0;i<svcc;i++)
    {
	ind=svind[i];
	cls[ind]=svcls[i];
    }

#pragma omp parallel private(i, j) firstprivate(X, m, svcc, sum, rsq, pa, kt, a, sam, svind)
#pragma omp for schedule(dynamic) nowait

    for(i=0;i<m;i++)
    {
	if (cls[i]<0)
	{
	    cls[i]=0;
	    for(j=0;j<svcc;j++)
	    {
		flag=adjcheck(X,  i,  svind[j],  sam,  a, kt,  pa, rsq, sum);
		if (flag)
		{
		    cls[i]=svcls[j];
		    break;
		}
	    }
	    if (j==svcc)
	    {
		cout<<"Label can not be found for the pixel"<<endl;
	    }
	}
    }

    // House keeping, eliminate (assign class label 0) to the clusters whose size are less than thd
    //consolidate(cls, m, (int)(m*.005), nc);
    consolidate(cls, m, (int)(m*.01), nc);
    getsvfsvind(cls, svind, svcc, nc, svf);
    delete [] svcls;
}


int inducecluster_sv(int svcc, int* svind, int m, gsl_matrix* K, int* svcls, int* cls)
{
    int i, j, ind, mc;
    double dd, mindd;

#pragma omp parallel private(i, j, ind, dd, mindd, mc) firstprivate(cls, svcc, K, svind, m)
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<m;i++)
    {
	if (cls[i]!=0)
	{
	    mindd=-1;
	    for(j=0;j<svcc;j++)
	    {
		ind=svind[j];
		dd=gsl_matrix_get(K, i, i)-2*gsl_matrix_get(K, i, ind)+gsl_matrix_get(K, ind, ind);

		if (mindd<0 || dd<mindd)
		{
		    mindd=dd;
		    mc=svcls[j];
		}
	    }
	    cls[i]=mc;
	}
    }
}

// Create clusters according to coefficients array a
int createcluster_v1(gsl_matrix* X, double* a, gsl_rng* rng, int sam, int kt, double* pa, double rsq, double sum, double rvm, int& nc, int* cls)
{

    int m, i, j, k;
    bool *adj, *chk;
    size_t* sts;

    m=X->size2;

    adj = new bool[m];
    chk = new bool[m];

    sts=randomperm(rng, m);
    for(i=0;i<m;i++)
    {
	//cout<<"i="<<i<<" a[i]="<<a[i]<<"  rvm="<<rvm<<" diff="<<rvm-a[i]<<endl;
	if (a[i]==rvm)
	{
	    chk[i]=true;
	    cls[i]=0;
	}
	else
	{
	    chk[i]=false;
	}
    }

    nc=1;
    for(k=0;k<m;k++)
    {
	i=sts[k];
	if (chk[i])
	{
	    continue;
	}

	//cout<<"i="<<i<<endl;
	for(j=0;j<m;j++)
	{
	    adj[j]=false;
	}

#pragma	omp parallel private(j) firstprivate(i, m, X, a, kt, pa, rsq, sum, sam)
#pragma omp for schedule(dynamic) nowait
	for(j=0;j<m;j++)
	{
	    if (!chk[j])
	    {
		adj[j]=adjcheck(X,  i,  j,  sam,  a, kt,  pa, rsq, sum);
	    }
	}

	inducecluster_oned( adj,  chk, i, a, m, nc, cls, rvm);
    }

    delete [] adj;
    delete [] chk;
    delete [] sts;
    return 0;
}


// Create clusters according to coefficients array a
int createcluster_v2(gsl_matrix* X, gsl_matrix* K, double* a, int sam, int kt, double* pa, double rsq, double sum, double rvm, int& nc, int* cls)
{
    int i, j, m, svcc;

    bool **adj;
    int* svind;

    double esma=0.0001;

    svcc=0;

    m=X->size2;
    svind = new int[m];

    for(i=0;i<m;i++)
    {
	cls[i]=-1;
    }

    for(i=0;i<m;i++)
    {
	if (a[i]>0 && a[i]<rvm)
	    //if (a[i]>esma && rvm-a[i]>esma)
	    //if (a[i]>esma && a[i]<rvm)
	{
	    svind[svcc]=i;
	    svcc++;
	}
	else if (a[i]==rvm)
	{
	    cls[i]=0;
	}
    }

    creatematrix(adj, svcc, svcc);

    cout<<"svcc="<<svcc<<endl;
    nc=1;

#pragma omp parallel private(i, j) firstprivate(X, svcc, svind,  sam,  a, kt,  pa, rsq, sum)
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<svcc-1;i++)
    {
	for(j=i+1;j<svcc;j++)
	{
	    adj[i][j]=adjcheck(X,  svind[i],  svind[j],  sam,  a, kt,  pa, rsq, sum);
	    adj[j][i]=adj[i][j];
	}
    }

    inducecluster_sv2(svcc, svind, adj, X, sam, a, kt, pa, rsq, sum,  nc, cls);

    deletematrix(adj, svcc);
    delete [] svind;
    return 0;
}

// Create clusters according to coefficients array a
int createcluster_v3(gsl_matrix* X, gsl_matrix* K,  int sam, int kt, double* pa, double rvm, int& nc, int* cls, svminfo* svf)
{
    int i, j, m, svcc;

    bool **adj;
    int* svind;
    double* a;
    double rsq;
    double sum;

    a=svf->a;
    rsq=svf->rsq;
    sum=svf->sum;


    double esma=0.0001;

    svcc=0;

    m=X->size2;
    svind = new int[m];

    for(i=0;i<m;i++)
    {
	cls[i]=-1;
    }

    for(i=0;i<m;i++)
    {
	if (a[i]>0 && a[i]<rvm)
	    //if (a[i]>esma && rvm-a[i]>esma)
	    //if (a[i]>esma && a[i]<rvm)
	{
	    svind[svcc]=i;
	    svcc++;
	}
	else if (a[i]==rvm)
	{
	    cls[i]=0;
	}
    }

    creatematrix(adj, svcc, svcc);

    cout<<"svcc="<<svcc<<endl;
    nc=1;

#pragma omp parallel private(i, j) firstprivate(X, svcc, svind,  sam,  a, kt,  pa, rsq, sum)
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<svcc-1;i++)
    {
	for(j=i+1;j<svcc;j++)
	{
	    adj[i][j]=adjcheck(X,  svind[i],  svind[j],  sam,  a, kt,  pa, rsq, sum);
	    adj[j][i]=adj[i][j];
	}
    }

    inducecluster_sv3(svcc, svind, adj, X, sam,  kt, pa,  nc, cls, svf);
    deletematrix(adj, svcc);
    delete [] svind;
    return 0;
}



int relables(int* cls, int m, double v, int& nc)
{

    int i, cc, upd, j, ind, k;
    double* nct;
    size_t* sts;
    bool* chk;	

    //    cout<<"v="<<v<<" nc="<<nc<<endl;
    nct=new double[nc];
    sts=new size_t[nc];
    chk=new bool[m];


    for(i=0;i<nc;i++)
    {
	nct[i]=0;
    }

    for(i=0;i<m;i++)
    {
	ind =cls[i];
	nct[ind]++;
	chk[i]=false;
	//	cout<<"i="<<i<<" ind="<<ind<<endl;
    }

    //    for(i=0;i<nc;i++)
    //    {
    //	cout<<"i="<<i<<"nct[i]="<<nct[i]<<endl;
    //    }

    gsl_sort_index(sts, nct, 1, nc);

    upd= (int) (m*v);
    cc=0;
    for(i=0;i<nc;i++)
    {
	ind=sts[i];
	cc+=(int) nct[ind];
	if (cc>upd)
	{
	    break;
	}
    }
    k=i;
    //    cout<<"k="<<k<<endl;
    cc=1;
    for(i=nc-1;i>=k;i--)
    {
	ind=sts[i];	
	for(j=0;j<m;j++)
	{
	    if (cls[j]==ind)
	    {
		cls[j]=cc;
		chk[j]=true;
	    }
	}
	//	cout<<"ind="<<ind<<" cc="<<cc<<endl;
	cc++;
    }

    //    cout<<"cc="<<cc<<endl;
    for(j=0;j<m;j++)
    {
	if (!chk[j])
	{
	    cls[j]=0;
	}
    }


    delete [] nct;
    delete [] sts;
    delete [] chk;

    //    cout<<"j="<<j<<endl;
    nc=cc;
}


int adjustcluster(int* cls, int nc, gsl_matrix* K)
{

    int i, j, m, k, p, ss;

    m=K->size2;

    double* ksums;
    double minksd, ksd;
    int** cdex;
    int* css;

    css=new int[nc];
    ksums=new double[nc];

    for(i=0;i<nc;i++)
    {
	css[i]=0;
    }

    creatematrix(cdex, nc, m);

    for(i=0;i<m;i++)
    {
	if (cls[i]>0)
	{
	    p= cls[i];
	    k = css[p];
	    cdex[p][k]=i;
	    css[p]++;
	}
    }

    for(i=1;i<nc;i++)
    {
	ss=css[i];
	ksums[i]=0;
	for(p=0;p<ss;p++)
	{
	    for(k=0;k<ss;k++)
	    {
		ksums[i]+=gsl_matrix_get(K, cdex[i][p], cdex[i][k]);
	    }
	}
	ksums[i]/=(ss*ss);
    }

#pragma omp parallel private(i, j, minksd, ksd) firstprivate(m, nc, cls, K, css, cdex, ksums)
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<m;i++)
    {
	if (cls[i]>0)
	{
	    minksd=DBL_MAX;
	    for(j=1;j<nc;j++)
	    {
		ksd=diskcore(K, i, cdex[j], css[j], ksums[j]);
		if (ksd<minksd)
		{
		    cls[i]=j;
		    minksd=ksd;
		}
	    }
	}
    }

    deletematrix(cdex, nc);
    delete [] css;
    delete [] ksums;


    return 0;
}

double diskcore(gsl_matrix* K, int i, int *cdexj, int ss,  double ksumj)
{
    int j, p;

    double sum, dms;

    sum=gsl_matrix_get(K, i, i) + ksumj;
    dms=0;
    for(p=0;p<ss;p++)
    {
	j=cdexj[p];
	dms+=gsl_matrix_get(K, i, j);
    }

    dms=dms*2/ss;

    return sum-dms;
}


// See if there clusters can be merged
int mergeclusters(gsl_rng* rng, int* cls, int ps, int sam, double* a, gsl_matrix* X, int kt, double* pa, double rsq, double sum, int& nc)
{

    int i, j, cc, m, ss, k, cur, mc, ind, p, nmcc, mincs, h;

    int *indlist1, *indlist2, *c1, *c2, *pnd, *nmlistcc;
    double*  dcls;
    double  cpr, cth;
    size_t* sts;

    bool* adj, *chk;
    bool flag, f2;
    int** nmlist;


    m=X->size2;
    ss=(nc-1)*nc*ps/2; 

    sts=new size_t[m];
    chk=new bool[nc];
    dcls=new double[m];
    pnd=new int[nc];
    nmlistcc=new int[nc];

    creatematrix(nmlist, nc, nc);  

    //for(i=0;i<m;i++)
    //{
    //	cout<<cls[i]<<endl;
    //    }

    for(i=0;i<nc;i++)
    {	
	for(j=0;j<nc;j++)
	{
	    nmlist[i][j]=0;
	}
	nmlistcc[i]=0;
    }

    for(i=0;i<m;i++)
    {
	dcls[i]=(double) cls[i];
    }

    gsl_sort_index(sts, dcls, 1, m);

    mc=0;
    cc=0;
    for(i=0;i<m;i++)
    {
	ind=sts[i];
	if (cls[ind]!=mc)
	{
	    pnd[cc]=i;
	    mc++;
	    cc++;
	}
    }
    pnd[nc-1]=m;

    /*
       for(i=0;i<nc;i++)
       {
       cout<<"cluster#"<<i<<": ";
       if (i==0)
       {
       cout<<pnd[0];
       }
       else
       {
       cout<<pnd[i]-pnd[i-1];
       }
       cout<<" pixels"<<endl;
       }

     */

    indlist1=new int[ss];
    indlist2=new int[ss];

    c1=new int[ss];
    c2=new int[ss];

    adj=new bool[ss];

    cur=0;
    for(i=1;i<nc;i++)
    {
	for(j=i+1;j<nc;j++)
	{
	    addsamples(rng, indlist1, cur, ps, i, pnd, sts);
	    addsamples(rng, indlist2, cur, ps, j, pnd, sts);
	    for(k=0;k<ps;k++)
	    {
		c1[k+cur]=i;
		c2[k+cur]=j;
		adj[k+cur]=false;
	    }
	    cur+=ps;
	}
    }

    ss=cur;

#pragma omp parallel private(i) firstprivate(ss, adj, X, indlist1, indlist2, sam, a, kt, pa, rsq, sum)
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<ss;i++)
    {
	adj[i]=adjcheck(X, indlist1[i], indlist2[i], sam, a, kt,  pa, rsq, sum);
    }


    cth=.55;
    nmcc=0;

    for(k=1;k<nc;k++)
    {
	for(p=k+1;p<nc;p++)
	{	
	    cc=0;
	    for(i=0;i<ss;i++)
	    {
		if (adj[i] && c1[i]==k && c2[i]==p)
		{
		    //cout<<"cluster"<<"#"<<c1[i];
		    //cout<<" and ";
		    //cout<<"cluster"<<"#"<<c2[i];
		    //cout<<" should be merged."<<endl;
		    cc++;

		}
	    }
	    cpr=cc/((double)ps);
	    // cout<<"Connectivity: "<<k<<"<--->"<<p<<"  Pr. = "<<cpr<<endl;

	    if  (cpr>cth)
	    {	
		flag=true;
		for(i=0;i<nmcc;i++)
		{
		    ind=nmlistcc[i];
		    for(j=0;j<ind;j++)
		    {
			if (nmlist[i][j]==p )
			{
			    f2=true;
			    for(h=0;h<ind;h++)
			    {
				if (nmlist[i][h]==k)
				{
				    f2=false;
				    break;
				}
			    }
			    if (f2)
			    {
				nmlist[i][ind]=k;
				nmlistcc[i]++;
				flag=false;
				break;
			    }
			}
			else if ( nmlist[i][j]==k)
			{
			    f2=true;
			    for(h=0;h<ind;h++)
			    {
				if (nmlist[i][h]==p)
				{
				    f2=false;
				    break;
				}
			    }
			    if (f2)
			    {
				nmlist[i][ind]=p;
				nmlistcc[i]++;
				flag=false;
				break;
			    }
			}
		    }
		}
		if (flag)
		{
		    nmlist[nmcc][0]=p;
		    nmlist[nmcc][1]=k;
		    nmlistcc[nmcc]=2;
		    nmcc++;
		}
	    }

	}
    }

    for(i=0;i<nc;i++)
    {
	chk[i]=false;
    }

    cc=1;
    mincs=(int)(m*0.01);

    /*
       for(i=0;i<nmcc;i++)
       {
       sum=0; 
       for(j=0;j<nmlistcc[i];j++)
       {
       ind=nmlist[i][j];
       sum+=pnd[ind]-pnd[ind-1];
       cout<<ind<<" ";
       }
       cout<<" sum="<<sum<<" mincs="<<mincs<<endl;
       }
     */

    for(i=0;i<nmcc;i++)
    {
	sum=0; 
	for(j=0;j<nmlistcc[i];j++)
	{
	    ind=nmlist[i][j];
	    sum+=pnd[ind]-pnd[ind-1];
	}
	if (sum>mincs)
	{
	    for(j=0;j<nmlistcc[i];j++)
	    {
		ind=nmlist[i][j];
		for(k=pnd[ind-1];k<pnd[ind];k++)
		{
		    p=sts[k];
		    cls[p]=cc;
		}
		chk[ind]=true;
	    }
	    cc++;
	}
    }

    for(i=1;i<nc;i++)
    {
	if (!chk[i] && pnd[i]-pnd[i-1]>mincs)
	{
	    for(k=pnd[i-1];k<pnd[i];k++)
	    {
		p=sts[k];
		cls[p]=cc;
	    }
	    chk[i]=true;
	    cc++;
	}
    }

    for(i=1;i<nc;i++)
    {
	if (!chk[i])
	{
	    for(k=pnd[i-1];k<pnd[i];k++)
	    {
		p=sts[k];
		cls[p]=0;
	    }
	    chk[i]=true;
	}
    }


    deletematrix(nmlist, nc);  

    nc=cc;

    delete [] indlist1;
    delete [] indlist2;
    delete [] c1;
    delete [] c2;
    delete [] adj;
    delete [] sts;
    delete [] dcls;
    delete [] pnd;
    delete [] chk;
    delete [] nmlistcc;

}



int addsamples(gsl_rng* rng, int* list, int cur, int ps, int clabel, int* pnd, size_t* sts)
{
    int i, idx, edx, ind;

    double ss;

    if (clabel==0)
    {
	idx=0;
	edx=pnd[0];
    }
    else 
    {
	idx=pnd[clabel-1];
	edx=pnd[clabel];
    }

    ss=(double) (edx-idx);

    for(i=0;i<ps;i++)
    {
	ind=idx+(int)floor(gsl_rng_uniform(rng)*ss);
	list[cur]=sts[ind];
	cur++;
    }

    return 0;
}

// Using SVC algorithm to cluster a rectangle subset of an image, the rectangle is specified by the 
// coordinate of the top left corner (x, y) and the number of row and the number of the column of the
// subset row, and col
//
int clusterablock(double** data, int irow, int icol, int bands,  int x, int y, int row, int col,
	double v,  int kt, double* pa, int& nc, int*& cls, double ivd)
{

    int i, j, ss, dx, dy, pnum, dz, ind, b;

    gsl_matrix* X;


    if (x>=0 && y>=0 && x+row<=irow && y+col<=icol)
    {
	X=gsl_matrix_alloc(bands, row*col);	
    }
    else
    {
	return -1;
    }


    pnum=icol*irow;

    cout<<"pnum="<<pnum<<" b="<<bands<<endl;
    for (i=0;i<row;i++)
    {
	for(j=0;j<col;j++)
	{
	    dy=(i+x)*icol+j+y;
	    dz=i*col+j;
	    for(b=0;b<bands;b++)
	    {
		gsl_matrix_set(X, b, dz, data[b][dy]);
		//cout<<data[b][dy]<<" ";
	    }
	    //cout<<endl;
	}
    }


    SVclustering_wf(X,   v,   kt,  pa,  nc, cls, ivd);

    gsl_matrix_free(X); 
    return 0;
}


int clusteroneimage(double** data, int natb, int icol, int irow, int bs, double v, int kt, double* pa, int& nc, int*& cls, double ivd, string oimgfname)
{

    gsl_matrix* X;

    bool flag;
    bool* vflags, *succ;
    short *rsflags;
    int i, j, k, m, ind, snc, sam, cc, pp, psp, pnum, width, h, maxcls, mvl, uncls, olduncls, newlab, nsnum;
    int cx1, cx2, cx3, stallcc, newnc, vl, tnc;
    int* scls, *idx, *cdcls, *kdex, *pxind, *wpc, *map, *untc;
    int** ncmap;
    size_t* sts;
    double ss, sr, vf, drsq;
    double* mcc;
    float* wcls;
    gsl_rng* rng;
    svminfo *svf;
    ofstream fimgout;



    rng=gsl_rng_alloc(gsl_rng_taus);
    gsl_rng_set(rng, time(NULL));
    pnum=icol*irow;
    maxcls=10000;  // Maximum number of clusters
    vf=0.25;   // Portion of clustered pixels to be overlapped with unclustered pixels


    cdcls=new int[pnum];
    cls=new int[pnum];
    wcls=new float[pnum];
    pxind=new int[pnum];
    untc=new int[pnum];

    vflags=new bool[pnum];
    rsflags=new short[pnum];
    succ=new bool[pnum];
    //wpc=new int[maxcls];

    olduncls=0;
    for(i=0;i<pnum;i++)
    {
	flag=true;
	for(j=0;j<natb;j++)
	{
	    if (data[j][i]<=ivd)
	    {
		flag=false;
		break;
	    }
	}
	if (flag)
	{
	    cls[i]=0;
	    olduncls++;
	}
	else
	{
	    cls[i]=-999;
	}
    }

    nsnum=(int)(olduncls*.15);  // The cut off # when the algorithm stop the clustering process (i.e., assume there are this number
    // noisy pixels in the image    

    idx=new int[bs];
    scls=new int[bs];

    svf = createsvminfo(bs);

    m=samplingaset(rng, cls, pnum, idx, bs);
    X=gsl_matrix_alloc(natb, m);

    cout<<"m="<<m<<" natb="<<natb<<endl;
    for(i=0;i<m;i++)
    {
	ind=idx[i];
	for(j=0;j<natb;j++)
	{
	    gsl_matrix_set(X, j, i, data[j][ind]);
	}
    }


    SVclustering(X,  v,  kt, pa, snc, scls, svf);

    // assign class labels found by the SVC algorithm
    for(i=0;i<m;i++)
    {
	ind=idx[i];
	cls[ind]=scls[i];
    } 




    cout<<"svf->svnum="<<svf->svnum<<endl;

    // for(i=0;i<svf->svnum;i++)
    // {
    //	cout<<svf->svind[i]<<" ";
    //  }
    //  cout<<endl;

    cout<<"svf->nc="<<svf->nc<<endl;
    for(i=1;i<svf->nc;i++)
    {
	cout<<svf->svcuts[i]<<" ";
    }
    cout<<endl;



    k=10; // # of nearest neighbours going to look for
    //sam=30;
    sam=25;
    width=15;

#pragma omp parallel private(i) firstprivate(pnum)
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<pnum;i++)
    {
	succ[i]=false;
	rsflags[i]=0;
    }

#pragma omp parallel private(i, ind) firstprivate(bs)
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<bs;i++)
    {
	if (scls[i]>0)
	{
	    ind=idx[i];
	    vflags[ind]=true;
	}
    }

    stallcc=0;
    nc=1;

    cout<<"nc="<<nc<<" snc="<<snc<<endl;
    while(true)
    {
	// Check if neighbours (spatially and spectrally close) of the newly clustered pixels belong to the same cluster
	psp=0;
	do
	{

#pragma omp parallel private(i) firstprivate(pnum)
#pragma omp for schedule(dynamic) nowait
	    for(i=0;i<pnum;i++)
	    {
		succ[i]=vflags[i];
	    }

#pragma omp parallel private(i) firstprivate(pnum)
#pragma omp for schedule(dynamic) nowait
	    for(i=0;i<pnum;i++)
	    {
		vflags[i]=false;
	    }


#pragma omp parallel private(i, j, ind, kdex) firstprivate(k, natb, pnum, icol, irow, width, sam, kt, pa, svf,X,data)
#pragma omp for schedule(dynamic) nowait
	    for(i=0;i<pnum;i++)
	    {
		if (succ[i] && rsflags[i]!=2)
		{
		    kdex=knnindex(data, icol, irow, natb, i,  width, k, cls, sam, kt, pa, svf, X, rsflags);
		    for(j=0;j<k;j++)
		    {
			ind=kdex[j];
			if (ind>=0)
			{
			    vflags[ind]=true;
			    cls[ind]=cls[i];
			}
			else
			{
			    break;
			}
		    }
		    delete [] kdex;
		}
	    }

	    cc=0;
	    for(i=0;i<pnum;i++)
	    {
		if (vflags[i])
		{
		    cc++;
		}
	    }
	    cout<<"# of pixels newly clustered="<<cc<<endl;

	    pp=0;
	    for(i=0;i<pnum;i++)
	    {
		if (succ[i])
		{
		    pp++;
		}
	    }

	    sr = cc/((double) pp);

	    cout<<" # of seeds ="<<pp<<" sr="<<sr<<endl;
	    psp++;
	}while(cc>100);



	//m=samplingaset(rng, cls, pnum, idx, bs);
	/*
	   if (m<bs)
	   {
	   break;
	   }

	   for(i=0;i<nc;i++)
	   {
	   wpc[i]=0;   // Overlap class counters
	   }

	   cc=0;
	   uncls=0;
	   mvl=(int)(bs*vf/(nc-1));  //maximum # of overlapped pixels per class 

	   sts=randomperm(rng, pnum);
	   for(h=0;h<pnum;h++)
	   {
	   i=sts[h];
	   ind=cls[i];	
	   if (ind>0 && ind<nc)
	   {
	   if (wpc[ind]<mvl)
	   {
	   idx[cc]=i;
	   cc++;
	   wpc[ind]++;
	   }
	   }
	   else
	   {
	   uncls++;
	   }
	   }
	   delete [] sts;

	   cout<<"Max # of pixels for each clusters in X ="<<mvl<<endl; 
	   for(i=0;i<nc;i++)
	   {
	   cout<<wpc[i]<<" ";
	   }
	   cout<<endl;
	 */
	//	vl=cc;
	//cout<<"The # of overlapped pixels in X = "<<vl<<endl;
	//

	uncls=0;
	cx1=0;
	cx2=0;
	cx3=0;
	for(h=0;h<pnum;h++)
	{
	    ind=cls[h];	
	    if (ind==0)
	    {
		uncls++;
		if (rsflags[h]==0) 
		{
		    rsflags[h]= calrsflags(data, ind, kt, pa, svf->a, svf->rsq, svf->sum, X);
		}
		if (rsflags[h]==1)
		{
		    untc[cx1]=h;
		    cx1++;
		}
		else
		{
		    cx3++;
		}
	    }
	}



	cout<<"# of pixels clustered in this round = "<<olduncls-uncls<<endl;
	cout<<"#of pixels unclustered and checked and found within boundary= "<<cx1<<endl;
	cout<<"#of pixels unclustered and checked and found out of boundary= "<<cx3<<endl;
	cout<<uncls<<" pixels remain unclustered"<<endl;

	tnc=nc;  // temporary variable because nc is a reference variable

#pragma omp parallel private(h, i, j) firstprivate(sam, data, untc, kt, pa, X, svf, tnc, cx1)
#pragma omp for schedule(dynamic) nowait
	for(h=0;h<cx1;h++)
	{
	    i=untc[h];
	    j=checkcls(data, i, sam, kt, pa, X, svf);
	    if (j>0)
	    {
		cls[i]=tnc+j-1;
	    }
	}

	cx2=0;
	cx3=0;
	for(h=0;h<cx1;h++)
	{
	    i=untc[h];
	    ind=cls[i];
	    if (ind==0)
	    {
		cx2++;
	    }
	    else if (ind>0)
	    {
		cx3++;
	    }
	}

	cout<<"Out of total "<<cx1<<" unclustered pixels"<<endl;  
	cout<<cx2<<" remain unclustered (the alg. are unable to cluster it in existing cluster."<<endl;  
	cout<<cx3<<" have been successfully clustered."<<endl;  

	//if (olduncls-uncls<bs)
	//{
	//    break;
	//	}
	//else
	//{
	olduncls=uncls;
	//}

	nc+=snc-1;
	m=samplingexset(rng, cls, pnum, idx, bs, rsflags);
	for(i=0;i<m;i++)
	{
	    ind=idx[i];
	    for(j=0;j<natb;j++)
	    {
		gsl_matrix_set(X, j, i, data[j][ind]);
	    }
	}
#pragma omp parallel private(i) firstprivate(pnum)
#pragma omp for schedule(dynamic) nowait
	for(i=0;i<pnum;i++)
	{
	    vflags[i]=false;
	    succ[i]=false;
	    rsflags[i]=0;
	}

	//nc=snc;    
	SVclustering(X,  v,  kt, pa, snc, scls, svf);

	cout<<"nc="<<nc<<" snc="<<snc<<endl;
	// merging the old and the new class label
	/*
	   creatematrix(ncmap, nc, snc);
	   for(i=0;i<nc;i++)
	   {
	   for(j=0;j<snc;j++)
	   {
	   ncmap[i][j]=0;
	   }
	   }

	   for(h=0;h<vl;h++)
	   {
	   cx2=scls[h]; // new class label
	   if (cx2>0)
	   {
	   i=idx[h];
	   cx1=cls[i];  // existing class label
	   ncmap[cx1][cx2]++;
	   }
	   }

	   newnc=nc;
	   cout<<"nc="<<nc<<" snc="<<snc<<endl;

	   for(i=0;i<nc;i++)
	   {
	   for(j=0;j<snc;j++)
	   {
	   cout<<ncmap[i][j]<<" ";
	   }
	   cout<<endl;
	   }

	   mcc=new double[nc];
	   map=new int[snc];
	   for(j=1;j<snc;j++)
	   {
	   cc=0;
	   for(i=1;i<nc;i++)
	   {
	   if (ncmap[i][j]>0)
	   {
	   newlab=i;
	   cc++;
	   }
	   }
	   if (cc>1)
	   {

	   cout<<"Cluster #"<<j<<" sit among "<<cc<<" existing classes"<<endl;
	   for(i=0;i<nc;i++)
	   {
	   mcc[i]=(double) ncmap[i][j];
	   cout<<ncmap[i][j]<<" ";
	   }
	   cout<<endl;
	   newlab=gsl_stats_max_index(mcc, 1, nc);
	   cout<<"Cluster #"<<j<<" merge with cluster#"<<newlab<<endl;
	   }
	   else if (cc==1)
	   {
	   cout<<"Cluster #"<<j<<" will merge with existing cluster#"<<newlab<<endl;
	   }
	   else
	   {
	   newlab=newnc;
	   newnc++;
	   cout<<"Cluster #"<<j<<" become the newly created cluster#"<<newlab<<endl;
	   }
	   map[j]=newlab;
	   }
	//Mapping the cluster labels to new cluster labels
	for(i=vl;i<bs;i++)
	{
	    j=scls[i];
	    if (j>0)
	    {
		scls[i]=map[j];
	    }
	}

	deletematrix(ncmap, nc);
	delete [] mcc;
	delete [] map;
	*/

	    for(i=0;i<bs;i++)
	    {
		j=scls[i];
		if (j>0)
		{
		    scls[i]=nc+j-1;
		}
	    }



#pragma omp parallel private(i, ind) firstprivate(bs)
#pragma omp for schedule(dynamic) nowait
	for(i=0;i<bs;i++)
	{
	    if (scls[i]>0)
	    {
		ind=idx[i];
		cls[ind]=scls[i];  // assign class labels found by the SVC algorithm
		vflags[ind]=true;
	    }
	}


	stallcc++;
	//if (stallcc>10)

#pragma omp parallel private(i) firstprivate(pnum)
#pragma omp for schedule(dynamic) nowait
	for(i=0;i<pnum;i++)
	{
	    wcls[i]=cls[i];
	}

	cout<<"Start writing results to the output file"<<endl;
	fimgout.open(oimgfname.c_str(), ios::out|ios::binary);
	if (fimgout.good())
	{
	    cout<<"Successfully open output file "<<oimgfname<<endl;
	    fimgout.write((char*)wcls, pnum*sizeof(float));
	    fimgout.close();
	}
	else
	{
	    cout<<"Fail to open output file "<<oimgfname<<endl;
	}

	if (uncls<nsnum)
	{
	    break;
	}
    }

    deletesvminfo(svf);
    //delete [] wpc;
    delete [] idx;	    
    delete [] untc;	    
    delete [] cdcls;	    
    delete [] scls;	    
    delete [] wcls;	    
    delete [] vflags;	    
    delete [] rsflags;	    
    delete [] succ;	    
    delete [] pxind;	    
    gsl_rng_free(rng);
    return 0;
}

int calrsflags(double** data, int i, int kt, double* pa, double *a, double rsq, double sum, gsl_matrix* X)
{
    int j, natb;
    double drsq;

    gsl_vector* px;

    natb=X->size1;
    px=gsl_vector_alloc(natb);

    for(j=0;j<natb;j++)
    {	    
	gsl_vector_set(px, j, data[j][i]);
    }
    drsq=calrsq(px, a, X,  kt, pa, sum);
    gsl_vector_free(px);

    if (drsq>rsq)
    {
	return 2;
    }
    else
    {
	return 1;
    }

}


int samplingexset(gsl_rng* rng, int* cls, int pnum, int* idx, int bs, short* rsflags)
{
    int i, m, ind;
    size_t* sts;

    m=0;
    sts=randomperm(rng, pnum);
    for(i=0;i<pnum;i++)
    {
	ind=sts[i];
	if (cls[ind]==0 && rsflags[ind]==2)
	{
	    idx[m]=ind;
	    m++;
	    if (m==bs)
	    {
		break;
	    }
	}
    }
    delete [] sts;
    return m;


}



int samplingaset(gsl_rng* rng, int* cls, int pnum, int* idx, int bs)
{
    int i, m, ind;
    size_t* sts;

    m=0;
    sts=randomperm(rng, pnum);
    for(i=0;i<pnum;i++)
    {
	ind=sts[i];
	if (cls[ind]==0)
	{
	    idx[m]=ind;
	    m++;
	    if (m==bs)
	    {
		break;
	    }
	}
    }
    delete [] sts;
    return m;
}

// Find k nearest neighbours of the pixel with index# ind 
int* knnindex(double** data, int icol, int irow, int natb, int ind,  int width, int k, int* cls, int sam, int kt, double* pa, svminfo* svf, gsl_matrix* X, short* rsflags)
{
    int i, j, h, pnum,cc, r, c, r1, c1, r2, c2, bp;	
    double df, sum, rsq, dsum, drsq;
    double* md;
    double *a;
    bool adj;
    size_t* sts;

    int* knnidx, *pxind;
    gsl_vector *pi, *pj, *px;

    px=gsl_vector_alloc(natb);
    pi=gsl_vector_alloc(natb);
    pj=gsl_vector_alloc(natb);


    pnum=(2*width)*(2*width);
    knnidx = new int [k]; 
    md=new double[pnum];
    sts=new size_t[pnum];
    pxind=new int[pnum];

    a=svf->a;
    sum=svf->sum;
    rsq=svf->rsq;


    for(j=0;j<natb;j++)
    {
	gsl_vector_set(pi, j, data[j][ind]);
    }

    r=ind/icol;    
    c=ind%icol;

    r1=r-width;
    if (r1<0)
    {
	r1=0;
    }

    c1=c-width;
    if (c1<0)
    {
	c1=0;
    }

    r2=r+width;
    if (r2>irow)
    {
	r2=irow;
    }

    c2=c+width;
    if (c2>icol)
    {
	c2=icol;
    }

    if (c2-c1<2*width)
    {
	if (c1==0)
	{
	    c2=c1+2*width;
	}
	else
	{
	    c1=c2-2*width;
	}
    }

    if (r2-r1<2*width)
    {
	if (r1==0)
	{
	    r2=r1+2*width;
	}
	else
	{
	    r1=r2-2*width;
	}
    }

    cc=0;
    for(i=r1;i<r2;i++)
    {
	for(j=c1;j<c2;j++)
	{
	    pxind[cc]=i*icol+j;
	    cc++;
	}
    }

    //   cout<<"ind="<<ind<<" ";
    //   cout<<r1<<" ";
    //   cout<<c1<<" ";
    //   cout<<r2<<" ";
    //   cout<<c2<<" ";
    //   cout<<endl;

    //#pragma omp parallel private(i, j, sum, df) firstprivate(pnum, natb, ind)
    //#pragma omp for schedule(dynamic) nowait

    for(h=0;h<pnum;h++)
    {
	i=pxind[h];
	if (cls[i]==0 && i!=ind )
	{
	    if (rsflags[i]==0)
	    {
		for(j=0;j<natb;j++)
		{	    
		    gsl_vector_set(px, j, data[j][i]);
		}
		drsq=calrsq(px, a, X,  kt, pa, sum);
		if (drsq>rsq)
		{
		    rsflags[i]=2;
		}
		else
		{
		    rsflags[i]=1;
		}
	    }
	    if (rsflags[i]!=2)
	    {
		dsum=0;
		for(j=0;j<natb;j++)
		{
		    df=data[j][ind]-data[j][i];
		    dsum+=df*df;
		}
		md[h]=dsum;
	    }
	    else
	    {
		md[h]=DBL_MAX;
	    }
	}
	else
	{
	    md[h]=DBL_MAX;
	}
    }

    //    cout<<"before sorting..."<<endl;
    gsl_sort_index(sts, md, 1, pnum);
    for(h=0;h<k;h++)
    {
	knnidx[h]=-1;
    }
    cc=0;
    for(h=0;h<pnum;h++)
    {
	i=sts[h];
	if (md[i]!=DBL_MAX)
	{
	    bp=pxind[i];
	    for(j=0;j<natb;j++)
	    {
		gsl_vector_set(pj, j, data[j][bp]);
	    }
	    adj=adjcheck2v(pi, pj, a, kt, pa, sum, rsq, sam, X);
	    if (adj)
	    {
		knnidx[cc]=bp;
		cc++;
	    }
	}
	if (cc==k)
	{
	    break;
	}
    }

    gsl_vector_free(px);
    gsl_vector_free(pi);
    gsl_vector_free(pj);
    delete [] md;
    delete [] sts;
    delete [] pxind;
    return knnidx;
}


// House keeping, eliminate (assign class label 0) to the clusters whose size are less than thd
int consolidate(int* cls, int m, int thd, int& nc)
{

    int i, ind, cc;
    int* cnm, *map;
    cnm=new int[nc];
    map=new int[nc];
    for(i=0;i<nc;i++)
    {
	cnm[i]=0;
    }

    for(i=0;i<m;i++)
    {
	ind=cls[i];
	cnm[ind]++;
    }

    map[0]=0;
    cc=1;

    for(i=1;i<nc;i++)
    {
	if (cnm[i]>=thd)
	{
	    map[i]=cc;
	    cc++;
	}
	else
	{
	    map[i]=0;
	}
    }

    nc=cc;

    for(i=0;i<m;i++)
    {
	ind=cls[i];
	cls[i]=map[ind];
    }

    delete [] cnm;
    delete [] map;
    return nc;
}


int getsvfsvind(int* cls, int* svind, int svcc, int nc, svminfo* svf)
{
    int i, cc, ind, ss, pc, oldcc;
    double* svcls;
    size_t* sts;

    svcls = new double[svcc];
    sts   = new size_t[svcc];

    // Mapping the class label to pixel index
    for(i=0;i<svcc;i++)
    {
	ind=svind[i];
	svcls[i]=(double)cls[ind];
    }

    // Sorting the classes labels
    gsl_sort_index(sts, svcls, 1, svcc); 
    ss=0;
    pc=0;
    oldcc=0;
    for(i=0;i<svcc;i++)
    {
	ind=sts[i];
	cc=(int)svcls[ind];

	if (cc>0)
	{
	    if (cc>oldcc)
	    {
		svf->svcuts[pc]=ss;
		oldcc=cc;
		pc++;
	    }
	    svf->svind[ss] = svind[ind];
	    ss++;    
	}
    }
    svf->svcuts[pc]=ss;
    svf->nc=nc;
    svf->svnum=ss;
    delete [] svcls;
    delete [] sts;
    return 0;
}


int checkcls(double** data, int ind, int sam, int kt, double* pa, gsl_matrix* X, svminfo* svf)
{

    int i, j, bd, ed, natb, tg, ps, h, nc, lab;
    double sum, rsq;
    double* md;
    size_t* sts;
    bool adj;



    gsl_vector* px, *py, *pz;

    natb=X->size1;

    px=gsl_vector_alloc(natb);
    pz=gsl_vector_alloc(natb);

    for(i=0;i<natb;i++)
    {
	gsl_vector_set(px, i, data[i][ind]);
    }

    ps=svf->svnum;
    nc=svf->nc;
    rsq=svf->rsq;
    sum=svf->sum;

    md=new double[ps];
    sts=new size_t[ps];

    for(i=0;i<ps;i++)
    {
	tg=svf->svind[i];	
	py=&gsl_matrix_column(X, tg).vector;
	gsl_vector_memcpy(pz, px);
	gsl_vector_sub(pz, py);
	md[i]=gsl_blas_dnrm2(pz);
    }

    gsl_sort_index(sts, md, 1, ps);

    for(h=0;h<ps;h++)
    {
	i=sts[h];
	tg=svf->svind[i];	
	py=&gsl_matrix_column(X, tg).vector;
	adj=adjcheck2v(px, py, svf->a, kt, pa, sum, rsq, sam, X);
	if (adj)
	{
	    for(lab=1;lab<nc;lab++)
	    {
		bd=svf->svcuts[lab-1];    
		ed=svf->svcuts[lab];    
		if (i>=bd && i<ed)
		{
		    break;
		}
	    }
	    //cout<<"i="<<i<<" nc="<<nc<<" h="<<h<<" lab="<<lab<<endl;
	    break;
	}
    }

    gsl_vector_free(px);
    gsl_vector_free(pz);
    delete [] md;
    delete [] sts;

    if (adj)
    {
	return lab;
    }
    else
    {
	return 0;
    }
}


int clusteroneimage_v2(double** data, int natb, int pnum, int* scheme, double v, double tao, double olv, int& nc, int*& cls, double ivd)
{

    int i, j, kt, cc, vpnum, ind;
    double* pa;
    int* idx, *wcls; 
    bool flag;

    idx=new int[pnum];
    cls=new int[pnum];
    cout<<"pnum="<<pnum<<endl; 
    cc=0;
    for(i=0;i<pnum;i++)
    {
	flag=true;
	for(j=0;j<natb;j++)
	{
	    if (data[j][i]<=ivd)
	    {
		flag=false;
		break;
	    }
	}
	if (flag)
	{
	    cls[i]=0;
	    idx[cc]=i;
	    cc++;
	}
	else
	{
	    cls[i]=-999;
	}
    }

    vpnum=cc;
    cout<<"There are "<<vpnum<<" valid pixels out of "<<pnum<<" pixels in the input image."<<endl;
    cout<<"Start clustering all valid pixels in the image."<<endl;

    wcls=new int[vpnum];
    cluster_oneset(data, natb, vpnum, 0, scheme, v, tao, olv, idx, nc, wcls);	

    for(i=0;i<vpnum;i++)
    {
	ind=idx[i];
	cls[ind]=wcls[i];
    }

    delete [] wcls;
    delete [] idx;
    return 0;
}


int cluster_oneset(double** data, int natb, int pnum, int cr, int* scheme, double v, double tao, double olv, int* idx, int& nc, int*& cls)	
{
    int i, bs, ss, ind, j;
    int **cidx, **olidx, **scls, **ridx;
    int *ccdx, *olcdx, *snc, *cnm;
    if (cr<natb)
    {
	// Prepare 
	bs=scheme[cr];	

	scls=new int* [bs]; // cluster labels for each pixels from each (sub) clustering process  
	snc=new int[bs];  // No. of clusters created in each (sub) clustering process
	cls=new int[pnum];
	for(i=0;i<pnum;i++)
	{
	    cls[i]=0;
	}
	divideoneset(data, pnum, cr, bs, olv, idx, cidx, olidx, ccdx, olcdx, ridx); 
	for(i=0;i<bs;i++)
	{
	    cluster_oneset(data, natb, ccdx[i], cr+1, scheme, v, tao, olv, cidx[i], snc[i], scls[i]);	
	    // for(j=0;j<ccdx[i];j++)
	    // {	
	    //cout<<"j="<<j<<" After cluster, cidx[i][j]="<<cidx[i][j]<<endl;
	    // }
	}

	if (bs>1)
	{
	    nc=1;
	    for(i=0;i<bs-1;i++)
	    {
		cout<<"cp="<<i<<" pnum="<<pnum<<endl;
		//connclusters(i, olidx, olcdx, snc, scls, ridx, ccdx,  cls, nc);
		connclusters_v2(i, olidx, olcdx, snc, scls, ridx, ccdx,  cls, nc);
	    }
	}
	else
	{
	    nc=snc[0];
	    for(i=0;i<ccdx[0];i++)
	    {
		ind=cidx[0][i];
		cls[ind]=scls[0][i];
	    }
	}

	// Display class distributions for this slice of data
	cnm=new int[nc];
	for(i=0;i<nc;i++)
	{
	    cnm[i]=0;
	}
	for(i=0;i<pnum;i++)
	{
	    ind=cls[i];
	    cnm[ind]++;
	}
	cout<<pnum<<" pixels have been classified in this round, class distributions are listed below."<<endl;
	for(i=0;i<nc;i++)
	{
	    cout<<"class#"<<i<<" : "<<cnm[i]<<endl;
	}
	delete [] cnm;

	// Clean up
	deletematrix(cidx, bs);
	deletematrix(ridx, bs);
	deletematrix(scls, bs);
	if (bs>1)
	{
	    deletematrix(olidx, bs-1);
	    delete [] olcdx;
	}
	delete [] ccdx;
	delete [] snc;
	return 1;
    }
    else
    {
	cluster_atomset(data, natb, pnum, v, tao, idx, nc, cls);	
	return 0;
    }
}



int cluster_atomset(double** data, int natb, int pnum, double v, double tao, int* idx, int& nc, int*& cls)
{
    int kt, ind, i, j, ind1, ind2, k;
    double sigma,  sum, df;
    double* pa, *desc, *sg;
    gsl_matrix* X;
    svminfo* svf;
    double** dism;

    svf = createsvminfo(pnum);
    pa=new double[10];
    sg=new double[pnum];
    cls=new int[pnum];
    kt=1;

    X=gsl_matrix_alloc(natb, pnum);
    cout<<"Start clustering a subset, pnum="<<pnum<<endl;
    for(i=0;i<pnum;i++)
    {
	ind=idx[i];
	//cout<<"i="<<i<<" in atomic cluster, ind="<<ind<<endl;
	for(j=0;j<natb;j++)
	{
	    gsl_matrix_set(X, j, i, data[j][ind]);
	}
    }

    creatematrix(dism, pnum, pnum);
    sum=0;

#pragma omp parallel private(i, j, ind1, ind2, sum, df, k) firstprivate(pnum, natb)
#pragma omp for schedule(dynamic) nowait

    for(i=0;i<pnum-1;i++)
    {
	dism[i][i]=0;
	ind1=idx[i];
	for(j=i+1;j<pnum;j++)
	{
	    ind2=idx[j];
	    sum=0;
	    for(k=0;k<natb;k++)
	    {
		df=data[k][ind1]-data[k][ind2];
		sum+=df*df;
	    }
	    dism[i][j]=sum;
	    dism[j][i]=sum;
	}
    }
    dism[pnum-1][pnum-1]=0;

    k=10;

#pragma omp parallel private(i, j, sum, desc) firstprivate(pnum, k)
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<pnum;i++)
    {
	desc=new double[k];
	gsl_sort_smallest(desc, k, dism[i], 1, pnum);
	sum=0;
	for(j=1;j<k;j++)
	{
	    sum+=desc[j];
	}
	delete [] desc;
	sum/=(k-1);
	sg[i]=sqrt(sum);
    }

    sigma=0;
    for(i=0;i<pnum;i++)
    {
	sigma+=sg[i];
    }
    sigma/=pnum;
    sigma*=tao;
    cout<<"tao="<<tao<<" sigma="<<sigma<<" p="<<1/(2*sigma*sigma)<<endl;
    nc=1;
    pa[0]=1/(2*sigma*sigma);
    SVclustering(X,  v,  kt, pa, nc, cls, svf);

    deletematrix(dism, pnum);
    gsl_matrix_free(X);
    deletesvminfo(svf);
    delete [] sg;
    delete [] pa;


    return 0;
}

int connclusters_v2(int cp,  int** olidx, int* olcdx, int* snc, int** scls, int** ridx, int* ccdx,  int* cls, int& nc)
{
    int i, j, k, ind, c1, c2, d1, d2, cs, newnc, ind2, thd, nc1, nc2, jpc;
    double** mmap;
    int* mapnc, *mapcc1, *mapcc2, *jpm;
    int** conn;
    bool** adjm;
    bool flag;

    double rr, x1, x2, x3;

    if (cp==0)
    {
	for(i=0;i<ccdx[cp];i++)
	{
	    ind=ridx[cp][i];
	    cls[ind]=scls[cp][i];
	}
	nc=snc[cp];
    }

    nc2=snc[cp+1];

    cout<<"cp="<<cp<<"  nc="<<nc<<" snc[cp+1]="<<nc2<<endl;

    mapcc1=new int[nc];
    mapcc2=new int[nc2];

    creatematrix(conn, nc2, nc);
    creatematrix(mmap, nc2, nc);
    creatematrix(adjm, nc, nc);

    for(i=0;i<nc2;i++)
    {
	for(j=0;j<nc;j++)
	{
	    mmap[i][j]=0;
	    conn[i][j]=0;
	}
	mapcc2[i]=0;
    }

    for(j=0;j<nc;j++)
    {
	mapcc1[j]=0;
    }

    for(j=0;j<nc-1;j++)
    {
	for(k=j+1;k<nc;k++)
	{
	    adjm[j][k]=false;
	    adjm[k][j]=false;
	}
	adjm[j][j]=false;
    }
    adjm[nc-1][nc-1]=false;

    d1=olidx[cp][0];
    d2=olidx[cp][1];
    mapnc=new int[nc2];


    cout<<"d1="<<d1<<" d2="<<d2<<"  olcdx[cp]="<<olcdx[cp]<<endl;
    // Counting the overlapping hits
    cout<<"ccdx[cp]="<<ccdx[cp]<<"  ccdx[cp+1]="<<ccdx[cp+1]<<endl;
    for(i=0;i<olcdx[cp];i++)
    {
	ind=ridx[cp][i+d1];
	ind2=ridx[cp+1][i+d2];

	c1=cls[ind];
	c2=scls[cp+1][d2+i];

	if (c1>=0 && c2>=0)
	{
	    mmap[c2][c1]++;
	}
	if (c1>=0)
	{
	    mapcc1[c1]++;
	}
	if (c2>=0)
	{
	    mapcc2[c2]++;
	}
    }


    for(i=1;i<nc2;i++)
    {
	for(j=1;j<nc;j++)
	{
	    // The number of pixels which belong to cluster j in the existing hyper-rectangle and belong to cluster i 
	    // in the new hyper-rectangle 
	    x2=mmap[i][j];  
	    x1=mapcc1[j]-x2;
	    x3=mapcc2[i]-x2;
	    if (x1+x3<x2)
	    {
		conn[i][j] = 1;
		cout<<" old cls#="<<j<<" new cls#="<<i;
		cout<<" x1="<<x1<<" x3="<<x3<<" x1+x3="<<x1+x3<<" x2="<<x2<<" conn="<<conn[i][j]<<endl;
	    }

	    else
	    {
		conn[i][j] = 0;
	    }

	}
    }


    // Building the map 
    newnc=nc;

    for(i=1;i<nc2;i++)
    {
	flag=false;
	for(j=1;j<nc;j++)
	{
	    if (conn[i][j]==1)
	    {
		flag=true;
		mapnc[i]=j;
		cout<<"map cls#"<<i<<" to old cls#"<<mapnc[i]<<endl;
		break;
	    }
	}
	if (!flag)
	{
	    mapnc[i]=newnc;
	    cout<<"map cls#"<<i<<" to new cls#"<<mapnc[i]<<endl;
	    newnc++;
	}
    }

    for(i=0;i<ccdx[cp+1];i++)
    {
	ind=ridx[cp+1][i];
	cs=scls[cp+1][i];
	if (cs>0 && cls[ind]==0)
	{
	    cls[ind]=mapnc[cs];
	}
    }
    cout<<"nc="<<nc<<" newnc="<<newnc<<endl;

    cout<<"display map table"<<endl;
    // Generate the connectivity information among the old clusters
    for(i=1;i<nc2;i++)
    {
	for(j=1;j<nc-1;j++)
	{
	    for(k=j+1;k<nc;k++)
	    {
		if (conn[i][j]==1 && conn[i][k]==1)
		{
		    adjm[j][k]=true;	
		    adjm[k][j]=true;	
		}
	    }
	}
    }


    clusterfromgraph(adjm, nc, jpc, jpm);  // Generate the consolidation information of old clusters

    jpc--;
    for(i=0;i<jpc;i++)
    {
	jpm[i]--;
    }

    deletematrix(adjm, nc);

    nc=newnc;
    delete [] mapnc;
    delete [] mapcc1;
    delete [] mapcc2;
    delete [] jpm;

    deletematrix(mmap, nc2);
    deletematrix(conn, nc2);
}

int connclusters(int cp,  int** olidx, int* olcdx, int* snc, int** scls, int** ridx, int* ccdx,  int* cls, int& nc)
{
    int i, j, ind, c1, c2, d1, d2, cs, newnc, ind2, thd;
    double** mmap;
    int* mapnc, *mapcc;
    double rr;

    if (cp==0)
    {
	for(i=0;i<ccdx[cp];i++)
	{
	    ind=ridx[cp][i];
	    cls[ind]=scls[cp][i];
	}
	nc=snc[cp];
    }


    cout<<"cp="<<cp<<"  nc="<<nc<<" snc[cp+1]="<<snc[cp+1]<<endl;

    mapcc=new int[snc[cp+1]];
    creatematrix(mmap, snc[cp+1], nc);
    for(i=0;i<snc[cp+1];i++)
    {
	for(j=0;j<nc;j++)
	{
	    mmap[i][j]=0;
	}
	mapcc[i]=0;
    }



    d1=olidx[cp][0];
    d2=olidx[cp][1];
    mapnc=new int[snc[cp+1]];

    cout<<"d1="<<d1<<" d2="<<d2<<"  olcdx[cp]="<<olcdx[cp]<<endl;
    // Counting the overlapping hits
    cout<<"ccdx[cp]="<<ccdx[cp]<<"  ccdx[cp+1]="<<ccdx[cp+1]<<endl;
    for(i=0;i<olcdx[cp];i++)
    {
	ind=ridx[cp][i+d1];
	ind2=ridx[cp+1][i+d2];

	//	cout<<"i+d1="<<i+d1<<" ind1="<<ind;
	//	cout<<" i+d2="<<i+d2<<" ind2="<<ind2;
	c1=cls[ind];
	c2=scls[cp+1][d2+i];
	//	cout<<" c2="<<c2<<" c1="<<c1;
	//	if (ind==ind2)
	//	{
	//	    cout<<endl;
	//	}
	//	else
	//	{
	//	    cout<<" *** "<<endl;
	//	}

	if (c1>0 && c2>0)
	{
	    mmap[c2][c1]++;
	}
	if (c2>=0)
	{
	    mapcc[c2]++;
	}
    }

    //rr=0.5;
    rr=0.618;
    // Building the map 
    newnc=nc;

    cout<<"display map table"<<endl;
    for(i=1;i<snc[cp+1];i++)
    {
	thd=(int) (rr*mapcc[i]);
	cout<<"class#"<<i<<" total#:"<<mapcc[i]<<" threshold: "<<thd<<" dist: ";	
	for(j=0;j<nc;j++)
	{
	    cout<<mmap[i][j]<<" ";
	}
	ind=gsl_stats_max_index(mmap[i], 1, nc);

	if (mmap[i][ind]>thd)
	{
	    mapnc[i]=ind;
	    cout<<"map class="<<ind<<endl;
	}
	else
	{
	    mapnc[i]=newnc;
	    cout<<"map class="<<newnc<<endl;
	    newnc++;
	}
    }
    cout<<endl;


    for(i=0;i<ccdx[cp+1];i++)
    {
	ind=ridx[cp+1][i];
	cs=scls[cp+1][i];
	if (cs>0 && cls[ind]==0)
	{
	    cls[ind]=mapnc[cs];
	}
    }
    cout<<"nc="<<nc<<" newnc="<<newnc<<endl;
    nc=newnc;
    delete [] mapnc;
    delete [] mapcc;
    deletematrix(mmap, snc[cp+1]);
}

int divideoneset(double** data, int pnum, int cr, int bs, double v, int* idx, int**& cidx, int**& olidx, int*& ccdx,
	int*& olcdx, int**& ridx)
{

    int i, j, ss, cc, ps, be, ed, ind;
    double* mp;
    size_t* sts;

    cidx=new int*[bs];
    ridx=new int*[bs];
    ccdx=new int[bs];

    if (bs>1)
    {
	olidx=new int*[bs-1];
	olcdx=new int[bs-1];
    }

    if (bs==1)
    {
	cidx[0]=new int[pnum];
	ridx[0]=new int[pnum];
	ccdx[0]=pnum;    
	for(i=0;i<pnum;i++)
	{
	    cidx[0][i]=idx[i];
	    ridx[0][i]=i;
	}
	return 0;
    }

    mp=new double[pnum];
    sts=new size_t[pnum];

    for(i=0;i<pnum;i++)
    {
	ind=idx[i];
	mp[i]=data[cr][ind];
    }
    gsl_sort_index(sts, mp, 1, pnum);

    ss=pnum/bs;
    cc=(int) (ss*v/2);

    for(i=0;i<bs;i++)
    {
	if (i==0)
	{
	    be=0;
	}
	else
	{
	    be=i*ss-cc;
	}
	if (i==bs-1)
	{
	    ed=pnum;
	}
	else
	{
	    ed=(i+1)*ss+cc;
	}
	ps=ed-be;
	ccdx[i]=ps;
	cidx[i]=new int[ps];
	ridx[i]=new int[ps];
	for(j=0;j<ps;j++)
	{
	    ind=sts[be+j];
	    cidx[i][j]=idx[ind];
	    ridx[i][j]=ind;
	    if (idx[ind]<0)
	    {
		cout<<"Error, negative index, ind="<<ind<<endl;
	    }
	}
    }

    for(i=0;i<bs-1;i++)
    {
	olidx[i]=new int[2];
	olidx[i][0]=ccdx[i]-2*cc;
	olidx[i][1]=0;
	olcdx[i]=2*cc;
    }

    delete [] sts;
    delete [] mp;
    return 0;	
}

double* classcount(int* cls, int nc, int pnum)
{
    int i, ind;

    double *cnm;

    cnm=new double[nc];

    for(i=0;i<nc;i++)
    {
	cnm[i]=0;
    }

    for(i=0;i<pnum;i++)
    {
	ind= cls[i];	
	if (ind>0 && ind<nc)
	{
	    cnm[ind]++;
	}
    }
    return cnm;
}


double* classcount(float* cls, int nc, int pnum)
{
    int i, ind;

    double *cnm;

    cnm=new double[nc];

    for(i=0;i<nc;i++)
    {
	cnm[i]=0;
    }

    for(i=0;i<pnum;i++)
    {
	ind=(int) cls[i];	
	if (ind>0 && ind<nc)
	{
	    cnm[ind]++;
	}
    }
    return cnm;
}

int sortclusters(int* cls, int nc, int pnum)
{
    int i, ind;

    int* mmap;
    double *cnm;
    size_t* sts;

    mmap=new int[nc];
    sts=new size_t[nc];


    cnm=classcount(cls, nc, pnum);
    gsl_sort_index(sts, cnm, 1, nc);

    for(i=1;i<nc;i++)
    {
	mmap[sts[nc-i]]=i;
    }

    for(i=0;i<pnum;i++)
    {
	ind=cls[i];
	if (ind>0 && ind<nc)
	{
	    cls[i]=mmap[ind];
	}
    }
    delete [] sts;
    delete [] cnm;
    delete [] mmap;

    return 0;
}

int sortclusters(float* cls, int nc, int pnum)
{
    int i, ind;

    int* mmap;
    double *cnm;
    size_t* sts;

    mmap=new int[nc];
    sts=new size_t[nc];


    cnm=classcount(cls, nc, pnum);
    gsl_sort_index(sts, cnm, 1, nc);

    // for(i=1;i<nc;i++)
    // {
    //	cout<<cnm[i]<<" ";
    //  }
    //  cout<<endl;

    for(i=1;i<nc;i++)
    {
	mmap[sts[nc-i]]=i;
    }

    for(i=0;i<pnum;i++)
    {
	ind=(int)cls[i];
	if (ind>0 && ind<nc)
	{
	    cls[i]=(float)mmap[ind];
	}
    }
    delete [] sts;
    delete [] cnm;
    delete [] mmap;

    return 0;
}

int findnc(float* cls, int pnum)
{
    int i, nc, ind;
    nc=1;
    for(i=0;i<pnum;i++)
    {
	ind=(int)cls[i];
	if (ind>=nc)
	{
	    nc=ind+1;
	}
    }
    return nc;
}


// assign labels to pixels 
int assignotlabels(float** data, int natb, float* wcls, int nc, double* cnm, double thd, int irow, int icol, int width, int cth)
{
    int i, j, pnum, ind, pc;
    bool flag;
    int* cls;

    pnum=irow*icol;
    cls=new int[pnum];

    for(i=0;i<pnum;i++)
    {
	cls[i]=0;
    }

#pragma omp parallel private(i, flag, ind, pc) firstprivate(pnum, thd, cth, irow, icol, nc, natb, width)
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<pnum;i++)
    {
	//cout<<"i="<<i<<endl;
	flag=false;
	pc= (int) wcls[i];
	if (pc==0)
	{
	    flag=true;
	}
	else if (pc>0) 
	    //	if (pc>0) 
	{
	    if (thd>0 && cnm[pc]<thd)
	    {
		flag=true;
	    }
	}
	if (flag)
	{
	    ind = findclusterNN(data, natb, wcls, nc, i, irow, icol, width, cth);
	    cls[i] = ind;
	    // cout<<"i="<<i<<" ind="<<ind<<" pc="<<pc<<endl;
	}
    }


    for(i=0;i<pnum;i++)
    {
	if (cls[i]>0)
	{
	    wcls[i]=(float) cls[i];
	}
    }

    delete [] cls;

    return 0;
}


int findclusterNN(float** data, int natb, float* wcls, int nc, int ind, int irow, int icol, int width, int cth)
{
    int pnum, k, i, j, r, c, r1, c1, r2, c2, h, cp, cc, minind;

    double *md, *cnm;
    size_t* sts;
    int *pxind;
    double df, dsum, minsum;

    k=1;
    // k=11;

    pnum=(2*width)*(2*width);
    md=new double[pnum];
    sts=new size_t[pnum];
    pxind=new int[pnum];
    cnm=new double[nc];


    r=ind/icol;    
    c=ind%icol;

    r1=r-width;
    if (r1<0)
    {
	r1=0;
    }

    c1=c-width;
    if (c1<0)
    {
	c1=0;
    }

    r2=r+width;
    if (r2>irow)
    {
	r2=irow;
    }

    c2=c+width;
    if (c2>icol)
    {
	c2=icol;
    }

    if (c2-c1<2*width)
    {
	if (c1==0)
	{
	    c2=c1+2*width;
	}
	else
	{
	    c1=c2-2*width;
	}
    }

    if (r2-r1<2*width)
    {
	if (r1==0)
	{
	    r2=r1+2*width;
	}
	else
	{
	    r1=r2-2*width;
	}
    }

    cc=0;
    for(i=r1;i<r2;i++)
    {
	for(j=c1;j<c2;j++)
	{
	    pxind[cc]=i*icol+j;
	    cc++;
	}
    }

    cc=0;
    minsum=DBL_MAX;
    minind=-1;
    for(h=0;h<pnum;h++)
    {
	i=pxind[h];
	if (wcls[i]>0 && wcls[i]<=cth && i!=ind)
	{
	    dsum=0;
	    for(j=0;j<natb;j++)
	    {
		df=(double)(data[j][ind]-data[j][i]);
		dsum+=df*df;
	    }
	    md[h]=dsum;
	    if (dsum<minsum)
	    {
		minsum=dsum;
		minind=i;
	    }
	    cc++;
	}
	else
	{
	    md[h]=DBL_MAX;
	}

    }

    if (k>1)
    {
	gsl_sort_smallest_index(sts, k, md, 1, pnum);
	for(i=0;i<nc;i++)
	{
	    cnm[i]=0;
	}

	for(h=0;h<k;h++)
	{	
	    i=sts[h];	
	    if (md[i]<DBL_MAX)
	    {
		j=pxind[i];
		cp=(int)wcls[j];
		cnm[cp]++;
	    }
	}
	i=gsl_stats_max_index(cnm, 1, nc);
    }
    else if (k==1)
    {
	if (cc<5)
	{
	    cout<<"cc="<<cc<<endl;
	}
	i=(int)wcls[minind];
    }

    delete []  md;
    delete []  sts;
    delete []  pxind;
    delete []  cnm;
    return i;
}


// Divide 
int findcth(double* cnm, int nc)
{
    double msg, minmsg;
    double *kcnm;

    int i, p, cth;

    kcnm=new double[nc];

    for(i=0;i<nc;i++)
    {
	kcnm[i]=kcnm[nc-1-i];
    }

    for(i=3;i<nc-3;i++)
    {
	p=nc-i;
	msg=gsl_stats_variance(cnm, 1, i)*i+ gsl_stats_variance(kcnm, 1, p)*p;
	if (msg<minmsg)
	{
	    minmsg=msg;
	    cth=i;
	}
    }
    delete [] kcnm;
    return cth;
}

Rblock** createRBlist(float** data, int irow, int icol, int natb, int bs, float* wcls, int cth, int& nb, int& nrow, int& ncol)
{
    Rblock** RBlist;
    int i, j, bnum, rs, roff, cs, coff, px, py, bsx, bsy;

    nrow = irow/bs;
    ncol = icol/bs;
    bnum=nrow*ncol; 


    bsx=irow/nrow;
    bsy=icol/ncol;
    roff=irow%nrow;
    coff=icol%ncol;

    RBlist = new Rblock*[bnum]; 

    px=0;

    for(i=0;i<nrow;i++)
    {
	py=0;
	if  (i<roff)
	{
	    rs=bsx+1;
	}
	else
	{
	    rs=bsx;
	}

	for(j=0;j<ncol;j++)
	{
	    if	(j<coff)
	    {
		cs=bsy+1;
	    }
	    else
	    {
		cs=bsy;
	    }
	    RBlist[i*ncol+j]=createRblock(px, py, rs, cs, icol, natb, data, wcls, cth);	    
	    py+=cs;
	}
	px+=rs;
    }

    nb=bnum;
    return RBlist;
}

Rblock* createRblock(int px, int py, int rs, int cs, int icol, int natb, float** data, float* wcls, int cth)
{

    int i, j, x1, y1, x2, y2, ind, vp, seeds, pnum, cp;
    int* idx;
    double sum, df;
    double* norms;
    Rblock* Rb;

    Rb=new Rblock;
    vp=0;
    seeds=0;

    pnum=rs*cs;
    idx=new int[pnum];
    norms=new double[pnum];

    x1=px;
    x2=x1+rs;
    y1=py;
    y2=y1+cs;

    for(i=x1;i<x2;i++)
    {
	for(j=y1;j<y2;j++)
	{
	    ind = i*icol + j;
	    cp=(int) wcls[ind];
	    if (cp>=0)
	    {
		if (cp==0 || cp>cth)
		{
		    vp++;
		}
		else
		{
		    idx[seeds]=ind;
		    seeds++;
		}
	    }
	}
    }


    if (seeds>0)
    {
	for(i=0;i<seeds;i++)
	{
	    sum=0;
	    ind=idx[i];
	    for(j=0;j<natb;j++)
	    {
		df=(double)data[j][ind];
		sum+=df*df;
	    }
	    norms[i]=sum;
	}


	Rb->idx=new int[seeds];
	Rb->norms=new double[seeds];
	for(i=0;i<seeds;i++)
	{
	    Rb->idx[i]=idx[i];
	    Rb->norms[i]=norms[i];
	}

    }
    else
    {
	Rb->idx=NULL;
	Rb->norms=NULL;
    }
    Rb->seeds=seeds;
    Rb->vp=vp;
    Rb->x1=x1;
    Rb->x2=x2;
    Rb->y1=y1;
    Rb->y2=y2;

    delete [] idx;
    delete [] norms;
    return Rb;
}


int assignotlabels_v2(float** data, int irow, int icol, int natb, int bs, int cth, float* wcls)
{

    int i, nb, nrow, ncol, k, pnum;
    float* cls;
    Rblock** rblist;
    Rblock* rb;

    rblist=createRBlist(data,  irow,  icol, natb, bs, wcls, cth, nb, nrow, ncol);
    cout<<"nb="<<nb<<" nrow="<<nrow<<" ncol="<<ncol<<endl;
    pnum=icol*irow;
    cls=new float[pnum];

    /*
       int asum, vpsum, sdsum, rs, cs,cp, seeds, vp;
       asum=0;
       vpsum=0;
       sdsum=0;
       pnum=icol*irow;
       for(i=0;i<nb;i++)
       {
       rb=rblist[i];
       rs=rb->x2-rb->x1;
       cs=rb->y2-rb->y1;
    //cout<<"i="<<i;
    //	cout<<" x1="<<rb->x1<<" x2="<<rb->x2;
    //	cout<<" y1="<<rb->y1<<" y2="<<rb->y2<<endl;
    asum+=rs*cs;
    vpsum+=rb->vp;
    sdsum+=rb->seeds;
    }
    cout<<"asum="<<asum<<" pnum="<<irow*icol<<endl;
    vp=0;
    seeds=0;
    for(i=0;i<pnum;i++)
    {
    cp=(int)wcls[i];
    if (cp>=0)
    {
    if (cp==0 || cp>cth)
    {
    vp++;
    }
    else
    {
    seeds++;
    }
    }
    }

    cout<<"vpsum="<<vpsum<<" vp="<<vp<<endl;
    cout<<"sdsum="<<sdsum<<" seeds="<<seeds<<endl;
    //   */
    k=1;

#pragma omp parallel private(i, rb ) firstprivate(nb, rblist, nrow, ncol, icol, natb, data, wcls, cls, cth, k)
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<nb;i++)
    {
	rb=rblist[i];
	if (rb->vp>0)
	{
	    clsRblock(rblist, i,  nrow, ncol, icol, natb, data, wcls, cls, cth, k);
	}
    }

    for(i=0;i<pnum;i++)
    {
	if (wcls[i]==0 || wcls[i]>cth)
	{
	    wcls[i]=cls[i];
	}
    }

    delete [] cls;
    delRBlist(rblist, nb);  
    return 0;
}

size_t* findNNblocks(int x, int y, int nrow, int ncol, int n, gsl_rng* rng)
{
    size_t *perm, *sts;
    int i, j, m, tx, ty, cc;


    m=8*n;
    sts  = new size_t[m];
    perm = new size_t[m];

    sts=randomperm(rng, m);
    for(i=0;i<m;i++)
    {
	perm[i]=-1;
    }
    cc=0;
    //   tx=x-n;
    //   ty=y-n;
    for(i=x-n;i<=x+n;i++)
    {
	tx=(int)fabs(i-x);
	for(j=y-n;j<=y+n;j++)
	{
	    ty=(int)fabs(j-y);
	    if (tx==n || ty==n)
	    {

		if (i<0 || i>=nrow || j<0 || j>=ncol)
		{
		    perm[sts[cc]]=-1;
		}
		else
		{
		    perm[sts[cc]]=i*ncol+j;
		}
		cc++;
	    }
	}
    }

    delete [] sts;
    return perm;
}

int findYmatrix(Rblock** rblist, int bid, int natb, float** data, int nrow, int ncol, int thd, float* wcls, gsl_matrix*& Y, 
	gsl_vector*& ny, float*& ycls)
{
    Rblock* rb;
    int* idx;
    double* norms;

    gsl_rng* rng;
    size_t* perm;
    int sds, m, n, i, j, x, y, ind, cc;
    bool flag;
    rng=gsl_rng_alloc(gsl_rng_taus);
    gsl_rng_set(rng, time(NULL));
    idx=new int[10*thd];
    norms=new double[10*thd];

    flag=true;
    x=bid/ncol;
    y=bid%ncol;

    sds=0;
    rb=rblist[bid];
    if (rb->seeds>0)
    {
	for(j=0;j<rb->seeds;j++)
	{
	    idx[j]=rb->idx[j];
	    norms[j]=rb->norms[j];
	}
	sds+=rb->seeds;
	if (sds>thd)
	{
	    flag=false;
	}
    }

    n=1;
    if (flag)
    {
	do
	{
	    m=8*n;
	    perm=findNNblocks(x, y, nrow, ncol, n, rng);
	    for(i=0;i<m;i++)
	    {
		ind=perm[i];
		if (ind>=0)
		{
		    rb=rblist[ind];
		    if (rb->seeds>0)
		    {
			for(j=0;j<rb->seeds;j++)
			{
			    idx[sds]=rb->idx[j];
			    norms[sds]=rb->norms[j];
			    sds++;
			}
			if (sds>thd)
			{
			    flag=false;
			    break;
			}
		    }
		}
	    }
	    n++;
	    delete [] perm;
	}while(flag);
    }

    Y=gsl_matrix_alloc(natb,sds);
    ny=gsl_vector_alloc(sds);
    ycls=new float[sds];
    for(i=0;i<sds;i++)
    {
	gsl_vector_set(ny, i, norms[i]);
	ind=idx[i];
	ycls[i]=wcls[ind];
	for(j=0;j<natb;j++)
	{
	    gsl_matrix_set(Y, j, i, data[j][ind]);
	}
    }

    delete [] idx;
    delete [] norms;
    gsl_rng_free(rng);
    return sds;
}

float clsNNpix(int ind, float** data, int natb, int sds, gsl_matrix* Y, gsl_vector* ny, float* ycls, int cth, int k)
{
    int i, j, cp, cc;
    float ws;
    gsl_vector *nx, *vx;
    double sum, df, alp, beta;
    size_t* sts;
    double* md, *cnm;

    nx=gsl_vector_alloc(sds);
    vx=gsl_vector_alloc(natb);

    for(i=0;i<natb;i++)
    {
	df=(double)data[i][ind];
	gsl_vector_set(vx, i, df);
	sum+=df*df;
    }
    gsl_vector_set_all(nx, sum);
    gsl_vector_add(nx,ny);
    alp=-2.0;
    beta=1.0;
    gsl_blas_dgemv(CblasTrans, alp, Y, vx, beta, nx);
    if (k==1)
    {
	cp = gsl_vector_min_index(nx);
	//cout<<"cp="<<cp<<" ycls[cp]="<<ycls[cp]<<endl;
	ws=ycls[cp];
	if (ws==0 || ws>cth)
	{
	    cout<<" ******************* error *****************"<<endl;
	}
    }
    else
    {
	md=gsl_vector_ptr(nx, 0);
	sts=new size_t[sds];
	cnm=new double[cth+1];
	gsl_sort_index(sts, md, 1, sds);
	for(i=0;i<k;i++)
	{
	    cp=sts[i];
	    cc=(int)ycls[cp];
	    cnm[cc]++;
	}    
	ws=(float)gsl_stats_max_index(cnm, 1, cth+1);
	delete [] sts;
	delete [] cnm;
    }

    gsl_vector_free(nx);
    gsl_vector_free(vx);
    return ws;
}

int clsRblock(Rblock** rblist, int bid,  int nrow, int ncol, int icol, int natb, float** data, float* wcls, float* cls, int cth, int k)
{
    Rblock* rb;
    int i, thd, sds, n, m, j, ind, cp ;

    gsl_matrix* Y;
    gsl_vector *ny, *nx;
    float* ycls;

    thd=1500;
    sds=findYmatrix(rblist, bid, natb, data, nrow, ncol, thd, wcls, Y, ny, ycls);
    //cout<<"sds="<<sds<<endl;
    rb=rblist[bid];

    for(i=rb->x1;i<rb->x2;i++)
    {
	for(j=rb->y1;j<rb->y2;j++)
	{
	    ind=i*icol+j;
	    //cout<<"i="<<i<<" j="<<j<<" ind="<<ind<<" old wls="<<wcls[ind];
	    if (wcls[ind]==0 || wcls[ind]>cth)
	    {
		cls[ind]=clsNNpix(ind, data, natb, sds, Y, ny, ycls, cth, k);
	    }
	    //cout<<" new cls="<<cls[ind]<<endl;
	}
    }


    gsl_matrix_free(Y);
    gsl_vector_free(ny);
    delete [] ycls;
    return 0;
}


int delRBlist(Rblock** rblist, int nb)
{
    int i;

    for(i=0;i<nb;i++)
    {
	delRblock(rblist[i]);
    }
    delete [] rblist;
    return 0;
}

int delRblock(Rblock* rb)
{
    if (rb->seeds>0)
    {
	delete [] rb->idx;
	delete [] rb->norms;
    }
    delete rb;
    return 0;
}

int sortclusters(float* cls, float* vals, int nc, unsigned long pnum, bool des)
{
    int i, ind, cp;

    int* mmap;
    double *cnm, *cct;
    double df;
    size_t* sts;

    mmap=new int[nc];
    cnm=new double[nc];
    sts=new size_t[nc];

    for(i=0;i<nc;i++)
    {
	cnm[i]=0;
    }
    for(i=0;i<pnum;i++)
    {
	cp=(int) cls[i];
	if (cp>0 && cp<nc)
	{
	    df=(double) vals[i];
	    cnm[cp]+=df;
	}
    }
    cct=classcount(cls, nc, pnum);
    for(i=1;i<nc;i++)
    {
	cnm[i]/=cct[i];
    }
    cnm[0]=-DBL_MAX;

    gsl_sort_index(sts, cnm, 1, nc);

    for(i=0;i<nc;i++)
    {
	if (des)
	{
	    mmap[sts[nc-i]]=i;
	}
	else
	{
	    mmap[sts[i]]=i;
	}
    }

    for(i=0;i<nc;i++)
    {
	cout<<cnm[i]<<" original class#="<<i<<" map class#="<<mmap[i]<<" sort vals="<<cnm[sts[i]]<<endl;
    }
    cout<<endl;

    for(i=0;i<pnum;i++)
    {
	ind=(int)cls[i];
	if (ind>0 && ind<nc)
	{
	    cls[i]=(float)mmap[ind];
	}
    }
    delete [] sts;
    delete [] cnm;
    delete [] mmap;

    return 0;
}

int countneigbours(int pnum, int irow, int icol, float* wcls, int nc, int**& nbs)
{
    int i, j;

    creatematrix(nbs, nc, nc);
    for(i=0;i<nc;i++)
    {
	for(j=0;j<nc;j++)
	{
	    nbs[i][j]=0;
	}
    }

    for(i=0;i<4;i++)
    {
	cout<<"ty="<<i<<endl;
	countonetype(i, pnum, irow, icol, wcls, nc, nbs);
    }

    return 0;
}


int countonetype(int ty, int pnum, int irow, int icol, float* wcls, int nc, int** nbs)
{

    int x, y, ind, inc, i, j, px, py;

    if (ty==0)  // pair wise relationships of horizontal neighbours 
    {
	for(i=0;i<irow;i++)
	{
	    ind=i*icol;
	    for(j=0;j<icol-1;j++)
	    {
		x=(int)wcls[ind];		
		y=(int)wcls[ind+1];		
		if (x>0 && y>0)
		{
		    nbs[x][y]++;
		    nbs[y][x]++;
		}
		ind++;
	    }
	}
    }
    else if (ty==1) // pair wise relationships of vertical neighbours
    {
	for(j=0;j<icol;j++)
	{
	    ind=j;
	    inc=icol;
	    for(i=0;i<irow-1;i++)
	    {
		x=(int)wcls[ind];		
		y=(int)wcls[ind+inc];		
		if (x>0 && y>0)
		{
		    nbs[x][y]++;
		    nbs[y][x]++;
		}
		ind+=inc;
	    }
	}

    }
    else if (ty==2) // pair wise relationships of right-hand diagonal neighbours
    {
	for(i=0;i<icol-1;i++)
	{
	    px=0;
	    py=i;
	    inc=icol+1;
	    do 
	    {
		ind=px*icol+py;
		x=(int)wcls[ind];
		y=(int)wcls[ind+inc];
		if (x>0 && y>0)
		{
		    nbs[x][y]++;
		    nbs[y][x]++;
		}
		px++;
		py++;
	    }while(px<irow-1 && py<icol-1);
	}
	for(i=1;i<irow-1;i++)
	{
	    px=i;
	    py=0;
	    inc=icol+1;
	    do 
	    {
		ind=px*icol+py;
		x=(int)wcls[ind];
		y=(int)wcls[ind+inc];
		if (x>0 && y>0)
		{
		    nbs[x][y]++;
		    nbs[y][x]++;
		}
		px++;
		py++;
	    }while(px<irow-1 && py<icol-1);
	}


    }
    else if (ty==3) // pair wise relationships of left-hand diagonal neighbours
    {
	for(i=1;i<icol;i++)
	{
	    px=0;
	    py=i;
	    inc=icol-1;
	    do 
	    {
		ind=px*icol+py;
		x=(int)wcls[ind];
		y=(int)wcls[ind+inc];
		if (x>0 && y>0)
		{
		    nbs[x][y]++;
		    nbs[y][x]++;
		}
		px++;
		py--;
	    }while(px<irow-1 && py>0);
	}
	for(i=1;i<irow-1;i++)
	{
	    px=i;
	    py=icol-1;
	    inc=icol-1;
	    do 
	    {
		ind=px*icol+py;
		x=(int)wcls[ind];
		y=(int)wcls[ind+inc];
		if (x>0 && y>0)
		{
		    nbs[x][y]++;
		    nbs[y][x]++;
		}
		px++;
		py--;
	    }while(px<irow-1 && py>0);
	}

    }

    return 0;
}

int setoneband(int vpn, int* idx, float* dst, float* src)
{
    int i, ind;

    for(i=0;i<vpn;i++)
    {
	ind=idx[i];
	dst[i]=src[ind];
    }
    return 0;
}


int readvalidpixels(string imgfname, int pnum, int bands, float**& data, int*& idx, float ivd)
{
    ifstream fin;
    int i, vpn, cc;

    float* rawdata;
    bool* masks;
    masks = new bool[pnum];
    rawdata = new float[pnum];


    fin.open(imgfname.c_str(), ios::binary|ios::in);
    if (fin.good())
    {
	cout<<"Successfully open input image file "<<imgfname<<endl;
    }
    else
    {
	cout<<"Fail to open input image file "<<imgfname<<endl;
	return -1;
    }



    fin.read((char*)rawdata, pnum*sizeof(float));
    cc=0;
    for(i=0;i<pnum;i++)
    {
	if (rawdata[i]>ivd)
	{
	    masks[i] = true;
	    cc++;
	}
	else
	{
	    masks[i] = false;
	}
    }


    vpn=cc;
    idx=new int[vpn];
    creatematrix(data, bands, vpn);
    cc=0;
    for(i=0;i<pnum;i++)
    {
	if (masks[i])
	{
	    idx[cc]=i;
	    cc++;
	}
    }

    setoneband(vpn, idx, data[0], rawdata);

    for(i=1;i<bands;i++)
    {
	fin.read((char*)rawdata, pnum*sizeof(float));
	setoneband(vpn, idx, data[i], rawdata);
	//cout<<" Finish setting band "<<i+1<<endl;
    }

    fin.close();

    delete [] rawdata;
    delete [] masks;

    return vpn;
}

int findmatch(double* sums, float** data, int* idx, int vpn, int bands, float** sdata, int dj)
{
    int i, j, ind, md;
    float* vec, *scl;
    double ssum, tp, mindis; 
    bool flag;


    scl=new float[bands];
    for(i=0;i<bands;i++) 
    {
	scl[i]=100;
    }

    scl[4] = -100;
    scl[6] = 1;
    scl[9] = 1;
    scl[10] = 1;

    ssum=0;
    vec=new float[bands];
    for(i=0;i<bands;i++) 
    {
	vec[i]=sdata[i][dj]/scl[i];
	tp = (double) vec[i];
	ssum+=tp;
    }


    mindis=DBL_MAX;
    ind = -1;
    // cout<<" ssum="<<ssum<<" dj="<<dj<<endl;
    for(i=0;i<vpn;i++)
    {
	//if (ssum==sums[i])
	//{
	tp=fabs(ssum-sums[i]);
	if (tp < mindis)
	{
	    md=i;
	    mindis=tp;
	}
	/*
	   flag=true;
	   for(j=0;j<bands;j++)
	   {
	   if (vec[j]!=data[j][i])
	   {
	   flag=false;
	   break;
	   }
	   }
	   if (flag)
	   {
	   ind=idx[i];
	   cout<<" found one match. ind="<<ind<<endl;
	   break;
	   }
	 */
	//}
    }
    /*
       cout<<" mindis="<<mindis<<" ind="<<idx[md]<<endl;
       for(i=0;i<bands;i++)
       {
       cout<<vec[i]<<" "<<data[i][md]<<endl;
       }
     */
    delete [] vec;
    delete [] scl;
    ind=idx[md];
    return ind;
}


// to determine if a point (x,y) is inside a  convex polygon whose vertex are specified the array vx and vy, 
// nc is the number of the vertex, return -1 if the point is outside the polygon, 
// 0 if it is on one of the edge of the polygon, 1 if it is inside the polygon

int insidepolygon(double* vx, double* vy, int nc, double x, double y)
{
    int i;

    double x0, x1, y0, y1, p;
    bool edge;

    edge=false;


    for(i=0;i<nc;i++)
    {
	if (i==nc-1)
	{
	    x1=vx[0];
	    y1=vy[0];
	}
	else
	{
	    x1=vx[i+1];
	    y1=vy[i+1];
	}

	x0=vx[i];
	y0=vy[i];

	p=(y-y0)*(x1-x0)-(x-x0)*(y1-y0);
	//cout<<p<<" ";
	if (p>0)
	{
	    return -1;
	}
	else if (p==0)
	{
	    edge=true;
	}
    }

    if (edge)
    {
	return 0;
    }
    else
    {
	return 1;
    }
}

size_t readmaskfile(string fname, size_t pnum, char target, size_t*& idxlist)
{

    size_t i, cc, ss;    
    ifstream fin;
    char* mask;

    fin.open(fname.c_str(), ios::in|ios::binary);
    if (!fin.good())
    {
	cout<<"Can not open the input file "<<fname<<endl;
	return 0;
    }

    mask=new char[pnum];
    fin.read(mask, pnum*sizeof(char));
    cc=0;

    for(i=0;i<pnum;i++)
    {
	if (mask[i]==target)
	{
	    cc++;
	}
    }
    ss=cc;
    cc=0;
    if (ss>0)
    {
	idxlist=new size_t[ss];
	for(i=0;i<pnum;i++)
	{
	    if (mask[i]==target)
	    {
		idxlist[cc]=i;
		cc++;
	    }
	}
    }
    delete [] mask;
    return ss;
}

// 

int checksubts(double* ts, size_t bands, double* x, double* y, size_t stp, size_t slen, size_t mlen, size_t sendp, double ivd, double* sps)
{
    size_t i, k, vp, ss, cc;
    double xstep, c0, c1, cov00, cov01, cov11, sumsq;

    xstep=0.1;
    i=stp;
    vp=0;
    cc=0;
    do
    {
	if (ts[i]>ivd)
	{
	    x[vp]=cc*xstep;
	    y[vp]=ts[i];
	    vp++;
	}
	i++;
	cc++;
	if (i>=bands)
	{
	    mlen=vp;
	    break;
	}
    }while(vp<mlen);

    if (vp<slen)
    {
	//cout<<"vp="<<vp<<" slen="<<slen<<endl;
	return -1;
    }
    ss=vp-slen;
    cc=0;
    for(i=slen;i<mlen;i++)
    {
	gsl_fit_linear(x, 1, y, 1,i, &c0, &c1, &cov00, &cov01, &cov11, &sumsq);
	sps[cc*6]=c0;	//  initial value of the line
	sps[cc*6+1]=c1;	//  slope of the line
	sps[cc*6+2]=sumsq;  // Sum of square error
	sps[cc*6+3]=i;	// Number of valid points in the sequence
	sps[cc*6+4]=stp;	// index number of the first point of the sequence
	sps[cc*6+5]=x[i]/xstep;  // Length of the sequence
	cc++;
    }
    return ss;
}

int segmentts(short* raw, size_t idx, size_t bands, size_t pnum, size_t minlen, size_t minla, size_t endp, double ivd, double*& states)
{

    double* ts, *x, *y, *sps;
    double scale, msq, bestmsq;
    int ss;
    size_t i, j, cc, wp, vp, lbr, rbr, sc, sendp, pt;
    double bestst[6];
    bool found;

    scale=10000.0;
    sendp=endp+12;

    if (sendp>bands)
    {
	sendp=bands;
    }

    ts = new double[bands];
    x = new double[bands];
    y = new double[bands];
    states=new double[bands*6];
    sps=new double[6*bands];

    // Prepare the time series
    for(i=0;i<bands;i++)
    {
	ts[i] = raw[idx*bands+i]/scale;
    }

    pt=0;
    sc=0;
    wp=0;
    vp=0;
    do
    { 
	lbr = minlen;
	rbr = minla;
	bestmsq = DBL_MAX;
	do
	{
	    //  cout<<"before checksubts"<<", pt="<<pt<<" sc="<<sc<<" lbr="<<lbr<<" rbr="<<rbr<<endl;
	    ss = checksubts(ts, bands,  x,  y, pt, lbr,  rbr, sendp, ivd, sps);
	    //  cout<<"ss="<<ss<<endl;
	    if (ss>0)
	    {   
		found=false;
		for(i=0;i<ss;i++)
		{
		    msq = sps[i*6+2]/sps[i*6+3]; // mean square error
		    if (msq<bestmsq)
		    {
			bestmsq=msq;
			wp=i;
			for(j=0;j<6;j++)
			{
			    bestst[j]=sps[wp*6+j];
			}
			found=true;
		    }
		}

		//check if the length of sequence with best mean square error longer than half of the max lookahead last round  

		vp = (size_t) sps[wp*6+3];
		//	cout<<"wp="<<wp<<" vp="<<vp<<" bestmsq="<<bestmsq<<endl;

		if (vp*2<=rbr | !found)
		{
		    break;
		}
		else // continue lookahead 
		{
		    lbr=rbr;
		    rbr=vp*2;
		}
	    }
	    else
	    {
		break;
	    }
	}while(true);
	for(j=0;j<6;j++)
	{
	    states[sc*6+j]=bestst[j];
	}
	sc++;	// Add one state in the sequence 
	pt+=(size_t) bestst[5];	// move to next point in the time series
	//cout<<"Here, pt="<<pt<<endl;
    }while(pt<endp-minlen-1);



    delete [] ts;
    delete [] x;
    delete [] y;
    delete [] sps;

    return sc;
}


int assigndna(double* seginfo, size_t ss, size_t dnapt, double* ths, int* dims, char* dna)
{
    size_t i; 
    int j, k, dm, nt, ofs, cc, thdpt;

    dm=3;
    double du[3];

    for(i=0;i<ss;i++)
    {

	du[0]=seginfo[i*6+1];  // slope
	du[1]=seginfo[i*6+5];  // length
	du[2]=seginfo[i*6];    // initial value

	//cout<<du[0]<<" "<<du[1]<<" "<<du[2]<<endl;

	dna[dnapt+i]=0;
	ofs=1;
	thdpt=0;
	for(j=0;j<dm;j++)
	{
	    nt = dims[j];  // Number of threshold 
	    if (nt>0)
	    {
		for(k=0;k<nt;k++)
		{
		    if (k!=nt-1)
		    {
			if (du[j]>=ths[thdpt+k] && du[j]<ths[thdpt+k+1])
			{
			    dna[dnapt+i]+=(ofs*(k+1));
			    // cout<<"k="<<k<<endl;
			    break;
			}
		    }
		    else if (du[j]>=ths[thdpt+k])
		    {
			dna[dnapt+i]+=(ofs*(k+1));
		    }
		}
		thdpt+=nt;
		ofs*=(nt+1);
	    }
	}
	//cout<<(int)dna[dnapt+i]<<endl;
    }
    return 0;
}


int readsegmeta(string segmetafname, size_t vpnum, short*& segnum)
{
    ifstream fin;
    size_t segtotal;

    fin.open(segmetafname.c_str(), ios::binary);
    if (!fin.good())
    {
	cout<<"Fail to open input file "<<segmetafname<<endl;
	return -2;
    }
    cout<<"Reading time series segmentation meta file... "<<endl;

    segnum =new short[vpnum];
    fin.read((char*)segnum, vpnum*sizeof(short));
    fin.close();
    return 0;
}    

size_t readtsmeta(string metafname, size_t* mhead, size_t*& idxlist)
{

    size_t vpnum;
    ifstream fin;

    fin.open(metafname.c_str(), ios::binary);
    if (!fin.good())
    {
	cout<<"Fail to open input file "<<metafname<<endl;
	return -1;
    }
    cout<<"Reading time series subset meta file... "<<endl;
    fin.read((char*)mhead, 4*sizeof(size_t));


    vpnum=mhead[0];
    if (vpnum>0)
    {
	idxlist=new size_t[vpnum];
	fin.read((char*)idxlist, vpnum*sizeof(size_t));
	fin.close();
    }
    return vpnum;
}


int findcutpoints(size_t* hisg, size_t binnum, size_t ncp, size_t*& cpts)
{

    size_t i, j, regnum, tgsize, ss, cc;

    regnum=ncp+1;

    cpts=new size_t[ncp];

    ss=0;
    for(i=0;i<binnum;i++)
    {
	ss+=hisg[i];
    }

    tgsize = ss/regnum;

    cc=0;
    j=0;
    for(i=0;i<binnum;i++)
    {
	cc+=hisg[i];
	if (cc>tgsize)
	{
	    cpts[j]=i+1;
	    cc=0;
	    j++;
	    if (j==ncp)
	    {
		break;
	    }
	}
    }
    return 0;
}


// Find the corresponding sub-sequence given the start value and the length
int findsubseg(size_t st, size_t slen, size_t bands, size_t didx, size_t seglen, short* dnalen, size_t& dst, size_t& dlen)
{

    size_t i, j, cc, ss;

    size_t* marks;

    marks=new size_t[bands];
    /*
       cout<<st<<" ";
       cout<<slen<<" ";
       cout<<didx<<" ";
       cout<<seglen<<" ";
       cout<<" ------- "<<endl;
     */

    cc=0;
    for(i=0;i<seglen;i++)
    {
	//	cout<<dnalen[i+didx]<<" ";
	for(j=0;j<dnalen[i+didx];j++)
	{
	    marks[cc]=i;
	    cc++;
	    if (cc>=bands)
	    {
		break;
	    }
	}
    }
    //    cout<<endl;

    // index number of the first DNA sub-sequence 
    dst=marks[st]+didx;

    ss=st+slen;
    if (ss>=bands)
    {
	ss=cc;
    }

    //The length of the DNA sub-sequence
    dlen=marks[ss-1]-marks[st]+1;
    if (dlen>seglen)
    {
	dlen=seglen;
    }

    delete [] marks;

    // cout<<dst<<" "<<dlen<<"   ***  "<<"    ";
    return 0;
}

int readseglen_static(string segdatafname, size_t segtotal, short* dnalen)
{

    size_t i, j, cc, ss, blocksize;
    ifstream fin;

    double* segdata;    

    blocksize = 3000000;
    segdata = new double[blocksize*6];

    fin.open(segdatafname.c_str(), ios::binary);
    if (!fin.good())
    {
	cout<<"Fail to open input file "<<segdatafname<<endl;
	return -2;
    }

    cout<<"Reading time series segmentation data file... "<<endl;

    cout<<"Segtotal="<<segtotal<<endl;
    i=0;
    cc=0;
    ss=0;
    do 
    {
	if (i+blocksize>=segtotal)
	{
	    blocksize=segtotal-i;
	}
	fin.read((char*)segdata, blocksize*6*sizeof(double));

	for(j=0;j<blocksize;j++)
	{
	    dnalen[cc]=(short) segdata[j*6+5];
	    cc++;
	}
	i+=blocksize;
	if (i>=segtotal)
	{
	    break;
	}
    }while(true);

    fin.close();
    delete [] segdata;
    return 0;
}


int readseglen(string segdatafname, size_t segtotal, short*& dnalen)
{

    size_t i, j, cc, ss, blocksize;
    ifstream fin;

    double* segdata;    

    blocksize = 3000000;
    segdata = new double[blocksize*6];

    fin.open(segdatafname.c_str(), ios::binary);
    if (!fin.good())
    {
	cout<<"Fail to open input file "<<segdatafname<<endl;
	return -2;
    }

    cout<<"Reading time series segmentation data file... "<<endl;

    cout<<"Segtotal="<<segtotal<<endl;
    dnalen = new short[segtotal];
    i=0;
    cc=0;
    ss=0;
    do 
    {
	if (i+blocksize>=segtotal)
	{
	    blocksize=segtotal-i;
	}
	fin.read((char*)segdata, blocksize*6*sizeof(double));

	for(j=0;j<blocksize;j++)
	{
	    dnalen[cc]=(short) segdata[j*6+5];
	    cc++;
	    /*
	       if (segdata[j*6+4]==0)
	       {
	       ss=0;
	       cout<<endl;
	       }
	       cout<<(short)segdata[j*6+4]<<" ";
	       cout<<(short)segdata[j*6+5]<<" ";
	       ss+=segdata[j*6+5];
	       if (ss>256)
	       {
	       cout<<" >256, idx = "<<i+blocksize<<endl;
	       }
	     */
	}

	//cout<<endl;

	i+=blocksize;
	if (i>=segtotal)
	{
	    break;
	}
    }while(true);

    fin.close();
    delete [] segdata;
    return 0;
}

Node* createnode(int level, int ncp, size_t binnum, int tgd)
{
    Node* nd;
    size_t i;

    nd = new Node;
    nd->cutpoints=new short[ncp];
    nd->hisg=new size_t[binnum];
    nd->ncp=ncp;
    nd->level=level;
    nd->tgd=tgd;
    nd->binnum=binnum;
    for(i=0;i<binnum;i++)
    {
	nd->hisg[i]=0;
    }
    nd->sons=NULL;
    return nd;
}


int deletetree(struct Node* nd)
{
    int ncp, i;

    delete [] nd->cutpoints;
    delete [] nd->hisg;
    if (nd->sons==NULL)
    {
	return 0;
    }
    else
    {
	ncp= nd->ncp;
	for(i=0;i<ncp+1;i++)
	{
	    deletetree(nd->sons[i]);
	}
    }
    delete [] nd->sons;
    delete nd;
}


int createsonnodes(Node* nd, int level, int ncp, int binnum, int tgd)
{
    int i, nfson;

    if (nd->level == level-1)
    {
	nfson=nd->ncp+1;
	nd->sons=new Node*[nfson];
	for(i=0;i<nfson;i++)
	{
	    nd->sons[i]= createnode(level, ncp, binnum, tgd);
	}
	return 0;
    }
    else
    {
	nfson=nd->ncp+1;
	for(i=0;i<nfson;i++)
	{
	    createsonnodes(nd->sons[i], level, ncp, binnum, tgd);
	}
	return 0;
    }

}

short assignlabel(Node* nd, size_t idx, int nc,  short* bindata, short& label, int* digit)
{
    int i, ncp, aa, tgd, level;
    short val;
    char ct;

//    cout<<"node = "<<nd<<endl;
    tgd = nd->tgd;
//    cout<<"tgd="<<tgd;
    val=bindata[idx*nc+tgd];
//    cout<<"val="<<val;
    ncp=nd->ncp;
    for(i=0;i<ncp;i++)
    {
	if (val<nd->cutpoints[i])
	{
	    break;
	}
    }

    level=nd->level;
//    cout<<"level="<<level<<" "<<endl;
    label+=digit[level]*i;
    if (level == nc - 1)
    {
	return label;
    }
    else
    {
	assignlabel(nd->sons[i], idx, nc, bindata, label, digit);
    }
}


int write_anode(ofstream& fout, Node* nd)
{
    int i;

    fout.write((char*)&(nd->level), sizeof(int));
    fout.write((char*)&(nd->tgd), sizeof(int));
    fout.write((char*)&(nd->ncp), sizeof(int));
    fout.write((char*)&(nd->binnum), sizeof(size_t));
    fout.write((char*)nd->cutpoints, nd->ncp*sizeof(short));

    return 0;
}


int write_subtree(ofstream& fout, Node* nd, int nc)
{
    int i, nson;
    write_anode(fout, nd);
    if (nd->level<nc-1)
    {
	nson=nd->ncp+1;
	for(i=0;i<nson;i++)
	{
	    write_subtree(fout, nd->sons[i], nc);
	}
    }
    return 0;
}

int output_tree(string cutpoints_fname, Node* root, int nc)
{

    ofstream fout;

    fout.open(cutpoints_fname.c_str(), ios::binary);

    if (!fout.good())
    {
	cout<<"Can not open output file "<<cutpoints_fname<<endl;
	return -1;
    }

    write_subtree(fout, root, nc);

    fout.close();
    return 0;
}

int create_subtree(ifstream& fin, Node*& nd, int nc)
{
    int i, level, tgd, ncp, nfson;
    size_t binnum;


    fin.read((char*)&level, sizeof(int));
    fin.read((char*)&tgd, sizeof(int));
    fin.read((char*)&ncp, sizeof(int));
    fin.read((char*)&binnum, sizeof(size_t));

    nd=createnode(level, ncp, binnum, tgd);
    fin.read((char*)nd->cutpoints, ncp*sizeof(short));

    if (level<nc-1)
    {
	nfson=ncp+1;
	nd->sons=new Node*[nfson];
	for(i=0;i<nfson;i++)
	{
	    create_subtree(fin, nd->sons[i], nc);
	}
    }

    return 0;

}



int input_tree(string cutpoints_fname, Node*& root, int nc)
{
    ifstream fin;

    fin.open(cutpoints_fname.c_str());

    if (!fin.good())
    {
	cout<<"Can not open input file "<<cutpoints_fname<<endl;
	root=NULL;
	return -1;
    }

    create_subtree(fin, root, nc);

    fin.close();
    return 0;

}


// Generate DNA for one class 

short* gendna(string binfname, size_t blocksize, size_t sgn, int nc, int* digit, Node* root)
{

    short* dna;
    size_t idxpt, bite, j;
    short* bindata;
    short label;	
    ifstream fin;

    bindata =new short[nc*blocksize];
    dna=new short[sgn];

    idxpt=0;
    bite=blocksize;
    fin.open(binfname.c_str(), ios::binary);
    do
    {
	if (bite+idxpt>sgn)
	{
	    bite=sgn-idxpt;
	}
	fin.read((char*)bindata, nc*bite*sizeof(short));


	for(j=0;j<bite;j++)
	{
	    label=0;
	    assignlabel(root, j, nc,  bindata, label, digit);
	    dna[j+idxpt]=label;
	}
	idxpt+=bite;
	if (idxpt>=sgn)
	{
	    break;
	}
    }while(true);

    fin.close();
    delete [] bindata;
    return dna;

}

int getbandtimes(string bandnames, int bands, double* bandtimes)
{
    int i, pos, ss;
    string st, onepiece;
    struct tm* timeinfo;
    time_t rawtime;

    time (&rawtime);
    timeinfo=localtime(&rawtime);

    st=bandnames;

    for(i=0;i<bands;i++)
    {
	if (i!=bands-1)
	{
	    pos=st.find(',');	
	}
	else
	{
	    pos=0;
	}
	if (pos>0)
	{
	    onepiece=st.substr(0, pos);
	    ss=st.size();
	    st=st.substr(pos+1, ss-pos-1);
	}
	else
	{
	    onepiece=st;
	}
	pos=onepiece.find_first_not_of(' ');
	if (pos>0)
	{
	    ss=onepiece.size();
	    onepiece=onepiece.substr(pos, ss-pos);
	}

	timeinfo->tm_year=getatom(onepiece, 0, 4)-1900;
	timeinfo->tm_mon=getatom(onepiece, 5, 2)-1;
	timeinfo->tm_mday=getatom(onepiece,8, 2);
	timeinfo->tm_hour=getatom(onepiece, 11, 2);
	timeinfo->tm_min=getatom(onepiece, 14, 2);
	timeinfo->tm_sec=getatom(onepiece, 17, 2);
	bandtimes[i]=mktime(timeinfo);
    }

    return 0;
}


int gettoffs(double* alltoffs, long tosnum, long tcol, double* bandtimes, int bands, int lat, int lon, double*& toffs)
{
    long i, j, be, ed;

    double bt, ivd;

    ivd=-9999;

    toffs = new double[bands];
	
    for(i=0;i<bands;i++)
    {
	toffs[i]=ivd;
    }


    be=-1;
    ed=-1;

    for(i=0;i<tosnum;i++)
    {
	if (alltoffs[i*tcol] == lat && alltoffs[i*tcol+1]==lon)
	{
	    if (be<0)
	    {
		be=i;
	    }
	    else
	    {
		ed=i;
	    }
	}
    }
    if (be <0 || ed<0)
    {
	return 0;
    }

    for(j=0;j<bands;j++)
    {
	bt=bandtimes[j];

	for(i=be;i<ed;i++)
	{
	    if (alltoffs[i*tcol] == lat && alltoffs[i*tcol+1]==lon && alltoffs[i*tcol+2] == bt)
	    {
		toffs[j]= alltoffs[i*tcol+3]; 
		break;
	    }
	}

    }

    return 0;
}

int readtidaloffsets(string fname, long& tosnum, long& tcol, double*& data)
{


    struct tm* timeinfo;
    time_t rawtime, bandtime, gap, timeslice;
    ifstream fin;

    time (&rawtime);
    timeinfo=localtime(&rawtime);

    timeinfo->tm_year=1970-1900;
    timeinfo->tm_mon=0;
    timeinfo->tm_mday=1;
    timeinfo->tm_hour=0;
    timeinfo->tm_min=0;
    timeinfo->tm_sec=0;

    long i,j, ss, cc, pos, bands, ns, years, vbands, obands, rounds, block;

    char buf[1024*16];
//    double * data;
    string latlonst, latst, lonst, dtst, tidalst, st, onepiece; 
    tosnum =countlines(fname);
    tcol = 4;

    data = new double[4*tosnum];
    fin.open(fname.c_str(), ios::in);
    
    ss=0;
    cc=0;

    do 
    {
	fin.getline(buf, 1024*16, '\n');
	if (fin.eof())
	{
	    break;
	}
	st=buf;
	pos=st.find(',');
	if (pos<0)
	{
	    continue;
	}
	ss=st.size();
	latlonst = st.substr(0,pos);
	st=st.substr(pos+1, ss-pos-1); 
	latst=latlonst.substr(0,3);
	lonst=latlonst.substr(4,4);

	data[cc*4]=atof(latst.c_str());
	data[cc*4+1]=atof(lonst.c_str());
	
	
	ss=st.size();
	pos=st.find(',');
	if (pos<0)
	{
	    continue;
	}

	onepiece = st.substr(0,pos);
	tidalst=st.substr(pos+1, ss-pos-1); 
    
	timeinfo->tm_year= getatom(onepiece, 0, 4)-1900;
	timeinfo->tm_mon = getatom(onepiece, 5, 2)-1;
	timeinfo->tm_mday= getatom(onepiece, 8, 2);
	timeinfo->tm_hour= getatom(onepiece, 11, 2);
	timeinfo->tm_min = getatom(onepiece, 14, 2);
	timeinfo->tm_sec = getatom(onepiece, 17, 2);
	bandtime=mktime(timeinfo);

	data[cc*4+2]=(double) bandtime;
	data[cc*4+3]=atof(tidalst.c_str());
	cc++;

    }while(true);
    fin.close();

   // toffs = data;

    return 0;

}


int getatom(string st, int pos, int len)
{
    string atom;
    atom=st.substr(pos, len);
    //cout<<atoi(atom.c_str())<<" ";;
    return atoi(atom.c_str());

}

int findneighbours(double* toffs, long N, double ivd, long*& ngb) 
{

    size_t* sts;
    long i, j;
    double* data;
    double val;

    data = new double[N];
    sts  = new size_t[N];   

    ngb= new long[N*N];

    for(i=0;i<N;i++)
    {
	val=toffs[i];
	if (val!=ivd)
	{
	    for(j=0;j<N;j++)
	    {
		data[j]=fabs(toffs[j]-val);
	    }
	    gsl_sort_index(sts, data, 1, N); 

	    for(j=0;j<N;j++)
	    {
		ngb[i*N+j]=sts[j];
	    }
	}
	else
	{
	    for(j=0;j<N;j++)
	    {
		ngb[i*N+j]=(long)ivd;
	    }
	}
    }	

    delete [] data;
    delete [] sts;
}
