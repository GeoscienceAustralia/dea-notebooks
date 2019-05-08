#include "dtree.h"

using namespace std;

bool getbit(unsigned short val, int bit)
{

    bool flag;
    unsigned short tgt[]={1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32786};

    flag = (bool) (val & tgt[bit]);

    return flag;
}


double NDI_ab(double a, double b)
{
    return (a-b)/(a+b);
}

double S_NDI_ab(double a, double b)
{
    return 2*a*a/(a+b);
}

int generateind(double* data, size_t idx, long ans)
{
    double b1, b2, b3, b4, b5, b7;

    size_t pt;

    pt=idx*ans+6;

    b1=data[idx*ans];
    b2=data[idx*ans+1];
    b3=data[idx*ans+2];
    b4=data[idx*ans+3];
    b5=data[idx*ans+4];
    b7=data[idx*ans+5];



    data[pt]=NDI_ab(b4, b3);
    data[pt+1]=NDI_ab(b5, b2);
    data[pt+2]=NDI_ab(b5, b4);
    data[pt+3]=NDI_ab(b7, b2);
    data[pt+4]=NDI_ab(b7, b4);

    data[pt+5]=S_NDI_ab(b4, b3);
    data[pt+6]=S_NDI_ab(b5, b2);
    data[pt+7]=S_NDI_ab(b5, b4);
    data[pt+8]=S_NDI_ab(b7, b2);
    data[pt+9]=S_NDI_ab(b7, b4);

    return 0;
}

int generateind_10idx(double* data, size_t idx, long ans)
{
    double b1, b2, b3, b4, b5, b7;

    size_t pt;

    pt=idx*ans+6;

    b1=data[idx*ans];
    b2=data[idx*ans+1];
    b3=data[idx*ans+2];
    b4=data[idx*ans+3];
    b5=data[idx*ans+4];
    b7=data[idx*ans+5];


    data[pt]=b1-b2;
    data[pt+1]=b1+b2;
    data[pt+2]=NDI_ab(b2, b3);
    data[pt+3]=NDI_ab(b2, b4);

    return 0;
}


int generateind_water(double* data, size_t idx, long ans)
{
    double b1, b2, b3, b4, b5, b7;

    size_t pt;

    pt=idx*ans+6;

    b1=data[idx*ans];
    b2=data[idx*ans+1];
    b3=data[idx*ans+2];
    b4=data[idx*ans+3];
    b5=data[idx*ans+4];
    b7=data[idx*ans+5];
    data[pt]=NDI_ab(b2, b4);

    return 0;
}

double bandratio(int* data, long idx, long b1, long b2, long oss)
{

    double brt;

    double v1, v2;

    v1=(double)data[b1*oss+idx];
    v2=(double)data[b2*oss+idx];

    if (v1+v2 == 0)
    {
	brt=0;
    }
    else
    {
	brt = (v2-v1)/(v2+v1);
    }

    return brt;
}

double getnegpulse(double* sa, char* mask, long tsbands, long tidx)
{
    long i;
    double val, sum;

    double left, rht;

    val=sa[tidx];

    sum=0;
    for(i=tidx-1;i>=0;i--)
    {
	if (mask[i]==0 && sa[i]<0.2)
	{
	    left=sa[i];
	    if (left>val)
	    {
		sum+=(left-val);
		break;
	    }
	    else
	    {
		return 0;
	    }
	}
    }
    for(i=tidx+1;i<tsbands;i++)
    {
	if (mask[i]==0 && sa[i]<0.2)
	{
	    rht=sa[i];
	    if (rht>val)
	    {
		sum+=(rht-val);
		break;
	    }
	    else
	    {
		return 0;
	    }
	}
    }

    return sum;

}

double getpulse(double* sa, char* mask, long tsbands, long tidx)
{
    long i;
    double val, sum;

    double left, rht;

    val=sa[tidx];

    sum=0;
    for(i=tidx-1;i>=0;i--)
    {
	if (mask[i]==0)
	{
	    left=sa[i];
	    if (left<val)
	    {
		sum+=(val-left);
		break;
	    }
	    else
	    {
		return 0;
	    }
	}
    }
    for(i=tidx+1;i<tsbands;i++)
    {
	if (mask[i]==0)
	{
	    rht=sa[i];
	    if (rht<val)
	    {
		sum+=(val-rht);
		break;
	    }
	    else
	    {
		return 0;
	    }
	}
    }

    return sum;

}


int findnoise(double* sa, long* saidx, long cc, long ltb, long rhb, char maskval, char* mask)
{


    long i, j, cutpoint, idx;
    size_t* sts;

    double *ab, *ba;
    double sum, minsum, val;

    sts=new size_t[cc];
    ab=new double[cc];
    ba=new double[cc];


    gsl_sort_index(sts, sa, 1, cc);
    for(j=0;j<cc;j++)
    {
	idx=sts[j];
	ab[j]=sa[idx];
	idx=sts[cc-j-1];
	ba[j]=sa[idx];
    }



    minsum=-1;
    for(j=ltb;j<rhb;j++)
    {
	sum = gsl_stats_sd(ab, 1, j)*j + gsl_stats_sd(ba, 1, cc-j)*(cc-j);
	if (minsum<0 || sum<minsum)
	{
	    cutpoint=j;
	    minsum=sum;
	}
    }

    val = ab[cutpoint-1]+ ab[cutpoint];


    for(j=0;j<cc;j++)
    {
	if (sa[j]>val)
	{
	    idx=saidx[j];
	    mask[idx]=maskval;
	}
    }

    delete [] sts;
    delete [] ab;
    delete [] ba;

    return 0;
}


int findtsidx(time_t sttime, size_t endtime, time_t* bandtime, long tsbands, vector<long>& saidx)
{
    long i;

    time_t curtime;

    saidx.clear();

    for(i=0;i<tsbands;i++)
    {
	curtime = bandtime[i];
	if (curtime>=sttime && curtime<endtime)
	{
	    saidx.push_back(i);
	}
    }

    return 0;

}

int findkNN(long tsidx, double* bandall, time_t curtime, time_t width, time_t* bandtime, long tsbands, long N, vector<long>& knnidx)
{

    long i, j, k, nbb;

    double val;

    double* sa;
    size_t* sts;

    time_t sttime, endtime;

    sa = new double[tsbands];
    sts = new size_t[tsbands];


    knnidx.clear();

    vector<long> wwidx;


    sttime = curtime - width;
    endtime = curtime + width;
    findtsidx(sttime, endtime, bandtime, tsbands, wwidx);
    nbb=wwidx.size();
    val=bandall[tsidx];

    if (nbb>0)
    {
	for(j=0;j<nbb;j++)    	
	{
	    k=wwidx[j];
	    if (k!=tsidx)
	    {
		sa[j] = fabs(val-bandall[k]);
	    }
	    else
	    {
		sa[j]=DBL_MAX;
	    }
	}
	gsl_sort_index(sts, sa, 1, nbb);
	if (N>nbb)
	{
	    N=nbb;
	}
	for(j=0;j<N;j++)
	{
	    knnidx.push_back(wwidx[sts[j]]);
	}

    }


    delete [] sts;
    delete [] sa;

    return 0;
}



int kNNnoisefilter(long tsidx, char* mask, double* sa, time_t curtime, time_t width, time_t* bandtime, long tsbands, long N, int newlab)
{


    long pp, nn, j, k, lab;

    vector<long> knnidx;
    findkNN(tsidx, sa, curtime, width, bandtime, tsbands, N, knnidx);
    N=knnidx.size();
    pp=0;
    nn=0;
    for(j=0;j<N;j++)
    {
	k=knnidx[j];
	lab = (int) mask[k];

	if (lab==0)
	{
	    pp++;
	}
	else
	{
	    nn++;
	}
    }
    if (pp<=nn)
    {
	mask[tsidx]=newlab;
    }


    return 0;
}


int spatialdiff(long tsidx, long tsbands,  long irow, long icol, double* bandavg, double* spadiff)
{


    char mc, nlab;

    int newlab;


    long i, j, k, p, x, y, cc, pnum, pt;
    double val, sum, ivd, cur;

    pnum = irow*icol;


    ivd = -0.099;

    pt = tsidx*pnum;

    for(i=0;i<irow;i++)
    {
	for(j=0;j<icol;j++)
	{
	    val  = bandavg[pt+i*icol+j];
	    if (val > ivd)
	    {

		sum=0;
		cc=0;
		for(k=-1;k<=1;k++)
		{
		    for(p=-1;p<=1;p++)
		    {
			x=i+k;
			y=j+p;

			if (x>=0 && x<irow && y>=0 && y<icol)
			{
			    cur = bandavg[pt+x*icol+y];
			    if (cur > ivd)
			    {
				sum+=cur;
				cc++;
			    }
			}
		    }
		}
		if (cc>3)
		{
		    spadiff[pt+i*icol+j] = sum/cc;
		}   
		else
		{
		    spadiff[pt+i*icol+j] = ivd;
		}

	    }
	    else
	    {
		spadiff[pt+i*icol+j] = ivd;
	    }
	}
    }


    return 0;

}

int spatialfilter(long tsidx, long tsbands,  long irow, long icol, char* noisemask)
{

    char* mask, *newmask;

    int mc, nlab;

    int newlab;


    long i, j, k, p, x, y, cc, pnum;


    pnum = irow*icol;

    mask = new char[pnum];
    newmask = new char[pnum];


    for(i=0;i<pnum;i++)
    {
	mask[i] = noisemask[tsidx*pnum+i];
	newmask[i] = noisemask[tsidx*pnum+i];
    }

    double avglab;

    // cout<<"tsidx = "<<tsidx<<endl;
    for(i=1;i<irow-1;i++)
    {
	for(j=1;j<icol-1;j++)
	{
	    mc  = (int) mask[i*icol+j];
	    if (mc==1)
	    {
		continue;
	    }

	    cc=0;
	    newlab=0;
	    for(k=-1;k<=1;k++)
	    {
		for(p=-1;p<=1;p++)
		{
		    x=i+k;
		    y=j+p;

		    if (k!=0 || p!=0)
		    {
			nlab=(int) mask[x*icol+y];
			if (nlab==1)
			{
			    continue;
			}
			if (mc==0)
			{
			    if (nlab>=2)
			    {
				newlab+=nlab;
				cc++;
			    }
			}
			else
			{
			    if (nlab==0)
			    {
				cc++;
			    }
			}
		    }
		}
	    }
	    /*
	       if (tsidx==704)
	       {
	       cout<<i+1<<", "<<j+1<<", ";
	       cout<<"mc="<<mc;
	       cout<<", cc="<<cc;
	       }*/

	    if (cc>6)
	    {
		if (mc>=2)
		{
		    newmask[i*icol+j]=0;
		}
		else
		{
		    avglab = ((double) newlab)/cc+0.5;
		    newlab= (int) floor(avglab);
		    newmask[i*icol+j]=(char)newlab;
		}

		/*
		   if (tsidx==704)
		   {
		   cout<<", newlab="<<newlab;
		   }*/


	    }
	    /*
	       if (tsidx==704)
	       {
	       cout<<endl;
	       }
	       */
	}
    }


    for(i=0;i<pnum;i++)
    {
	noisemask[tsidx*pnum+i] = newmask[i];
    }





    delete [] mask;
    delete [] newmask;

    return 0;

}

long findpairs(double* sa, char* mask, long tsbands, long* paidx, double* pamu, int N)
{

    long i, j, k, cc, ss;

    double mu;

    ss=0;

    for(i=0;i<tsbands;i++)
    {
	cc=0;
	mu=0;
	for(j=i;j<tsbands;j++)
	{
	    if (mask[j]==0)
	    {
		paidx[ss*N+cc]=j;
		mu+=sa[j];
		cc++;
		if (cc==N)
		{
		    mu/=cc;
		    pamu[ss]=mu;
		    break;
		}
	    }
	}
	if (cc==N)
	{
	    ss++;
	}
	else
	{
	    break;
	}
    }

    return ss;

}

int testpair(double* sa, char* mask, double* dwi, long tsbands, long* paidx, long pp, long N)
{
    long i, j, k, lfb, rhb, pt, cc;

    double mid, mu, m1, m2, m3, cspkthd, sspkthd, cloudthd, shadowthd; 

    // cspkthd = 0.8;
    // sspkthd = 0.8;

    //  cspkthd = 0.7;
    //  sspkthd = 0.7;
    cspkthd = 0.63;
    sspkthd = 0.63;
    cloudthd = 0.14;
    //shadowthd = 0.035;
    shadowthd = 0.055;


    pt=pp*N;
    mu=0;

    cc=0;
    lfb=paidx[pt];
    rhb=paidx[pt+N-1];
    for(i=pt;i<pt+N;i++)
    {
	k = paidx[i];
	if (mask[k]==0)
	{
	    mu+=sa[k];
	    cc++;
	}
    }
    if (cc==0)
    {
	return -1;
    }

    m2=mu/cc;

    cc=0;
    mu=0;
    // looking at left of the time series
    for(i=lfb-1;i>=0;i--)
    {
	if (mask[i]==0)
	{
	    if (sa[i]>shadowthd || dwi[i]>0)
	    {
		mu+=sa[i];
		cc++;
		if (cc==N)
		{
		    m1=mu/cc;
		    break;
		}
	    }
	}
    }
    if (cc<N)
    {
	cc=0;
	mu=0;
	for(i=rhb+1+N*1.5;i<tsbands;i++)
	{
	    if (mask[i]==0)
	    {
		if (sa[i]>shadowthd || dwi[i]>0)
		{
		    mu+=sa[i];
		    cc++;
		    if (cc==N)
		    {
			m1=mu/cc;
			break;
		    }
		}
	    }
	}
    }

    cc=0;
    mu=0;
    for(i=rhb+1;i<tsbands;i++)
    {
	if (mask[i]==0)
	{
	    if (sa[i]>shadowthd || dwi[i]>0)
	    {
		mu+=sa[i];
		cc++;
		if (cc==N)
		{
		    m3=mu/cc;
		    break;
		}
	    }
	}
    }

    if (cc<N)
    {
	cc=0;
	mu=0;
	for(i=lfb-1-1.5*N;i>=0;i--)
	{
	    if (mask[i]==0)
	    {
		if (sa[i]>shadowthd || dwi[i]>0)
		{
		    mu+=sa[i];
		    cc++;
		    if (cc==N)
		    {
			m3=mu/cc;
			break;
		    }
		}
	    }
	}
    }


    mid=(m1+m3)/2;
    if (m2>mid)
    {
	if ((m2-mid)/mid> cspkthd && m2>cloudthd)			
	{
	    for(i=pt;i<pt+N;i++)
	    {
		k = paidx[i];
		mask[k]=3;
	    }
	}
    }
    else
    {
	if ((mid-m2)/m2> sspkthd && m2<shadowthd)			
	{
	    for(i=pt;i<pt+N;i++)
	    {
		k = paidx[i];
		mask[k]=2;
	    }
	}
    }

    return 0;
}






int spikeremoval(char* mask, double* dwi, double* sa, long tsbands, int N)
{

    long i, j, k, cc, ss;

    double val, minsum, sum, m1, m2, m3, mid, cspkthd, sspkthd, cloudthd, shadowthd; 

    cspkthd = 0.8;
    sspkthd = 0.8;
    cloudthd = 0.14;
    shadowthd = 0.035;


    if (N<1 || N > 3)
    {
	return -1;
    }


    long *paidx;
    double *pamu; 

    paidx  = new long[N*tsbands];
    pamu  = new double[tsbands];

    ss = findpairs(sa, mask, tsbands, paidx, pamu, N);

    if (ss<=0)
    {
	delete [] paidx;
	delete [] pamu;
	return -1;
    }

    size_t* sts;

    sts = new size_t[tsbands];

    gsl_sort_index(sts, pamu, 1, ss);


    for(i=ss-1;i>=0;i--)
    {
	k=sts[i];
	testpair(sa, mask, dwi, tsbands, paidx, k, N);
    }



    delete [] paidx;
    delete [] pamu;
    delete [] sts;


    return 0;	


}



int detectnoise_v2(double* bandavg, double* mndwi, long pidx, long pnum, long tsbands, char* noisemask, time_t* bandtime)
{
    double thd;
    double* sa, *dwi;
    long* saidx;
    size_t* sts;
    char* mask;
    long i, j, k;
    long cc, ss, sublen, idx, cutpoint;

    thd=-0.08;

    sa = new double [tsbands];
    dwi = new double [tsbands];
    mask = new char[tsbands];


    cc=0;
    for(i=0;i<tsbands;i++)
    {
	sa[i]=bandavg[i*pnum+pidx];
	dwi[i]=mndwi[i*pnum+pidx];
	if (sa[i]<thd)
	{
	    mask[i]=1;
	}
	else if (sa[i]>0.45)
	{
	    mask[i]=3;
	}
	else
	{
	    mask[i]=0;
	    cc++;
	}
    }


    spikeremoval(mask,  dwi,  sa, tsbands, 1);
    spikeremoval(mask,  dwi,  sa, tsbands, 1);
    spikeremoval(mask,  dwi,  sa, tsbands, 2);
    spikeremoval(mask,  dwi,  sa, tsbands, 2);
    spikeremoval(mask,  dwi,  sa, tsbands, 3);

    for(i=0;i<tsbands;i++)
    {
	noisemask[i*pnum+pidx]=mask[i];
    }

    delete [] mask;
    delete [] sa;
    delete [] dwi;


    return 0;
}

int detectnoise(double* bandavg, long pidx, long pnum, long tsbands, char* noisemask, time_t* bandtime, time_t width)
{
    double thd;
    double* sa;
    long* saidx;
    size_t* sts;
    char* mask;
    long i, j, k;
    long cc, ss, sublen, idx, cutpoint;

    thd=-0.09;

    sa = new double [tsbands];
    saidx = new long [tsbands];
    sts = new size_t[tsbands];
    mask = new char[tsbands];

    cc=0;
    for(i=0;i<tsbands;i++)
    {
	sa[i]=bandavg[i*pnum+pidx];
	if (sa[i]<0)
	{
	    mask[i]=1;
	}
	else if (sa[i]>0.45)
	{
	    mask[i]=6;
	}
	else
	{
	    mask[i]=0;
	    cc++;
	}
    }


    double val, minsum, sum; 

    //double *ab, *ba;
    //ab  = new double[tsbands];
    //ba  = new double[tsbands];

    sublen=tsbands/5+1;
    cc=0;
    ss=0;
    for(i=0;i<tsbands;i++)
    {
	if (mask[i]==0)
	{
	    sa[cc]=bandavg[i*pnum+pidx];
	    saidx[cc]=i;
	    cc++;
	}
	ss++;
	if (ss==sublen || i==tsbands -1)
	{
	    /*
	       minsum=-1;
	       gsl_sort_index(sts, sa, 1, cc);
	       for(j=0;j<cc;j++)
	       {
	       idx=sts[j];
	       ab[j]=sa[idx];
	       idx=sts[cc-j-1];
	       ba[j]=sa[idx];
	       }

	    // find the point with 
	    for(j=cc*0.2;j<cc*0.8;j++)
	    {
	    sum = gsl_stats_sd(ab, 1, j)*j + gsl_stats_sd(ba, 1, cc-j)*(cc-j);
	    if (minsum<0 || sum<minsum)
	    {
	    cutpoint=j;
	    minsum=sum;
	    }
	    }
	    val = ab[cutpoint-1]+ ab[cutpoint];

	    for(j=0;j<cc;j++)
	    {
	    if (sa[j]>val)
	    {
	    idx=saidx[j];
	    mask[idx]=1;
	    }
	    }

*/

	    findnoise(sa, saidx, cc, cc*0.2, cc*0.8, 6, mask);


	    ss=0;
	    cc=0;
	}

    }

    double* plus;
    plus=new double[tsbands];

    for(i=0;i<tsbands;i++)
    {
	sa[i] = bandavg[i*pnum+pidx];
	plus[i]=0;
    }



    for(i=1;i<tsbands-1;i++)
    {
	if (mask[i]==0)
	{
	    plus[i]=getpulse(sa, mask, tsbands, i);
	}
    }


    cc=0;
    for(i=0;i<tsbands;i++)
    {
	if (plus[i]>0)
	{
	    sa[cc]=plus[i];
	    saidx[cc]=i;
	    cc++;
	}
    }



    findnoise(sa, saidx, cc, cc*0.3, cc*0.8, 5, mask);


    for(i=0;i<tsbands;i++)
    {
	sa[i] = bandavg[i*pnum+pidx];
	plus[i]=0;
    }

    for(i=1;i<tsbands-1;i++)
    {
	if (mask[i]==0)
	{
	    plus[i]=getpulse(sa, mask, tsbands, i);
	}
    }


    cc=0;
    for(i=0;i<tsbands;i++)
    {
	if (plus[i]>0)
	{
	    sa[cc]=plus[i];
	    saidx[cc]=i;
	    cc++;
	}
    }

    findnoise(sa, saidx, cc, cc*0.3, cc*0.9, 5, mask);



    vector<long> knnidx;
    long N;

    int lab, pp, nn;


    for(i=0;i<tsbands;i++)
    {
	sa[i]=bandavg[i*pnum+pidx];
    }

    N=5;

    for(i=0;i<tsbands;i++)
    {
	if (mask[i]==0)
	{
	    kNNnoisefilter(i, mask, sa, bandtime[i], width, bandtime, tsbands, N, 4);
	}
    }

    N=5;

    for(i=0;i<tsbands;i++)
    {
	if (mask[i]==0)
	{
	    kNNnoisefilter(i, mask, sa, bandtime[i], width, bandtime, tsbands, N, 4);
	}
    }

    for(i=0;i<tsbands;i++)
    {
	sa[i] = bandavg[i*pnum+pidx];
	plus[i]=0;
    }

    for(i=1;i<tsbands-1;i++)
    {
	if (mask[i]==0 && sa[i]< 0.2)
	{
	    plus[i]=getnegpulse(sa, mask, tsbands, i);
	}
    }


    cc=0;
    for(i=0;i<tsbands;i++)
    {
	if (plus[i]>0)
	{
	    sa[cc]=plus[i];
	    saidx[cc]=i;
	    cc++;
	}
    }

    if (cc>5)
    {
	findnoise(sa, saidx, cc, cc*0.1, cc*0.85, 2, mask);
    }

    for(i=0;i<tsbands;i++)
    {
	sa[i]=bandavg[i*pnum+pidx];
    }

    N=5;

    for(i=0;i<tsbands;i++)
    {
	if (mask[i]==0 && sa[i]<0.09)
	{
	    kNNnoisefilter(i, mask, sa, bandtime[i], 10*width, bandtime, tsbands, N, 3);
	}
    }

    for(i=0;i<tsbands;i++)
    {
	sa[i]=bandavg[i*pnum+pidx];
    }

    N=5;

    for(i=0;i<tsbands;i++)
    {
	if (mask[i]==0 && sa[i]<0.09)
	{
	    kNNnoisefilter(i, mask, sa, bandtime[i], 10*width, bandtime, tsbands, N, 3);
	}
    }

    N=5;

    for(i=0;i<tsbands;i++)
    {
	if (mask[i]==0 && sa[i]<0.09)
	{
	    kNNnoisefilter(i, mask, sa, bandtime[i], 10*width, bandtime, tsbands, N, 3);
	}
    }

    for(i=0;i<tsbands;i++)
    {
	noisemask[i*pnum+pidx]=mask[i];
    }

    delete [] mask;
    delete [] sts;
    delete [] sa;
    //  delete [] ab;
    //  delete [] ba;
    delete [] plus;


    return 0;
}


int strtotime(string st, time_t& stime)
{
    string aast;

    struct tm* timeinfo;
    int year, month, day;
    time_t rawtime;


    aast=st.substr(0,4);
    year=atoi(aast.c_str());


    aast=st.substr(5,2);
    month=atoi(aast.c_str());


    aast=st.substr(8,2);
    day=atoi(aast.c_str());

    time (&rawtime);
    timeinfo=localtime(&rawtime);

    timeinfo->tm_year=year-1900;
    timeinfo->tm_mon=month-1;
    timeinfo->tm_mday=day;
    timeinfo->tm_hour=0;
    timeinfo->tm_min=0;
    timeinfo->tm_sec=0;
    timeinfo->tm_isdst=0;

    stime = mktime(timeinfo);

    return  0;
}


float windowidxmean(double* bandavg, long pidx, char* noisemask, long pnum, vector<long>& saidx)
{
    long i, ss, idx, cc;
    double sum, ivd;

    ss = saidx.size();

    ivd=-0.099;


    if (ss>10)
    {
	cc=0;
	sum=0;
	for(i=0;i<ss;i++)
	{
	    idx=saidx[i];
	    if (noisemask[idx*pnum+pidx]==0 && bandavg[idx*pnum+pidx] > ivd)
	    {
		sum+=bandavg[idx*pnum+pidx];
		cc++;
	    }
	}
	if (cc>0)
	{
	    sum/=cc;
	}
	else
	{
	    sum=0;
	}
	return sum;
    }
    else
    {
	return 0;
    }
}


float windowmean(double* bandavg, long pidx, char* noisemask, long pnum, time_t sttime, size_t endtime, time_t* bandtime, long tsbands)
{

    vector<long> saidx;

    findtsidx(sttime, endtime, bandtime, tsbands, saidx);
    return windowidxmean(bandavg, pidx, noisemask, pnum, saidx);
}

long predictchange(double* bandavg, long pidx, long pnum, long tsbands, time_t width, char* noisemask, time_t* bandtime, float* mva)
{

    double* sa;
    vector<long> saidx;

    long i, j, cc;

    time_t curtime, sttime, endtime;

    double max, val;


    cc=0;

    max=0;

    // max = gsl_stats_max(mva, 1, tsbands/3);

    for(i=tsbands/3;i<tsbands-10;i++)
    {
	val =  mva[i*pnum+pidx];
	if (val>max)
	{


	}
    }

    return 0;
}

long calchange_v3(double* bandavg, long pidx, long pnum, long tsbands, time_t width, char* noisemask, time_t* bandtime, float* mva, float* frwins, float* bkwins, double* evi)
{

    double* sa;
    vector<long> saidx;

    long i, j, cc;

    time_t curtime, sttime, endtime, mintime, maxtime;

    double mu, sd, lf_sum, rh_sum;


    mintime = bandtime[0];
    maxtime = bandtime[tsbands-1];


    cc=0;
    for(i=10;i<tsbands-10;i++)
    {
	curtime = bandtime[i];
	sttime = curtime - width;
	endtime = curtime;

	if (sttime>=mintime)
	{
	    lf_sum = windowmean(bandavg, pidx, noisemask, pnum, sttime, endtime, bandtime, tsbands);
	}
	else
	{
	    lf_sum=0;
	}

	sttime = curtime;
	endtime = curtime + width;
	if (endtime<maxtime)
	{
	    rh_sum = windowmean(bandavg, pidx, noisemask, pnum, sttime, endtime, bandtime, tsbands);
	}
	else
	{
	    rh_sum=0;
	}

	if (lf_sum==0 || rh_sum ==0)
	{
	    mva[i*pnum+pidx]=0;
	}
	else
	{
	    mva[i*pnum+pidx]= rh_sum - lf_sum;
	}

	curtime = bandtime[i];
	sttime = curtime - width;
	endtime = curtime;
	lf_sum = windowmean(evi, pidx, noisemask, pnum, sttime, endtime, bandtime, tsbands);

	sttime = curtime;
	endtime = curtime + width;
	rh_sum = windowmean(evi, pidx, noisemask, pnum, sttime, endtime, bandtime, tsbands);

	if (lf_sum==0 || rh_sum ==0)
	{
	    frwins[i*pnum+pidx]=0;
	    bkwins[i*pnum+pidx]=0;
	}
	else
	{
	    frwins[i*pnum+pidx]= lf_sum;
	    bkwins[i*pnum+pidx]= rh_sum;
	}

    }

    return 0;
}

long calchange_v2(double* bandavg, long pidx, long pnum, long tsbands, time_t width, char* noisemask, time_t* bandtime, float* mva, float* frwins, float* bkwins)
{

    double* sa;
    vector<long> saidx;

    long i, j, cc;

    time_t curtime, sttime, endtime;


    double mu, sd, lf_sum, rh_sum;

    cc=0;
    for(i=10;i<tsbands-10;i++)
    {
	curtime = bandtime[i];
	sttime = curtime - width;
	endtime = curtime;
	lf_sum = windowmean(bandavg, pidx, noisemask, pnum, sttime, endtime, bandtime, tsbands);

	sttime = curtime;
	endtime = curtime + width;
	rh_sum = windowmean(bandavg, pidx, noisemask, pnum, sttime, endtime, bandtime, tsbands);

	if (lf_sum==0 || rh_sum ==0)
	{
	    mva[i*pnum+pidx]=0;
	    frwins[i*pnum+pidx]=0;
	    bkwins[i*pnum+pidx]=0;
	}
	else
	{
	    mva[i*pnum+pidx]= rh_sum - lf_sum;
	    frwins[i*pnum+pidx]= lf_sum;
	    bkwins[i*pnum+pidx]= rh_sum;
	}
    }

    return 0;
}

long calchange(double* bandavg, long pidx, long pnum, long tsbands, time_t width, char* noisemask, time_t* bandtime, float* mva, float* absmva)
{

    double* sa;
    vector<long> saidx;

    long i, j, cc;

    time_t curtime, sttime, endtime;


    double mu, sd, lf_sum, rh_sum;

    cc=0;
    for(i=10;i<tsbands-10;i++)
    {
	curtime = bandtime[i];
	sttime = curtime - width;
	endtime = curtime;
	lf_sum = windowmean(bandavg, pidx, noisemask, pnum, sttime, endtime, bandtime, tsbands);

	sttime = curtime;
	endtime = curtime + width;
	rh_sum = windowmean(bandavg, pidx, noisemask, pnum, sttime, endtime, bandtime, tsbands);

	if (lf_sum==0 || rh_sum ==0)
	{
	    mva[i*pnum+pidx]=0;
	    absmva[i*pnum+pidx]=0;
	}
	else
	{
	    mva[i*pnum+pidx]= rh_sum - lf_sum;
	    absmva[i*pnum+pidx]= fabs(rh_sum - lf_sum);
	}
    }

    return 0;
}

long longtermchange_v3(float* mva, float* frwins, float* bkwins, float* spdev, long pidx, long pnum, long tsbands, time_t* bandtime, double* chprb, time_t* chtime, float* chscale, float* lfwins, float* rhwins)
{

    long i, maxidx;

    double* sa;

    double sp, thd, lfchange, rhchange;


    //thd = 0.3;
    thd = 0.7;
    //thd = 1.2;


    sa = new double[tsbands];

    for(i=0;i<tsbands;i++)
    {
	sa[i]=mva[i*pnum+pidx];
    }

    maxidx = gsl_stats_max_index(sa, 1, tsbands);

    sp = spdev[maxidx*pnum+pidx];

    chprb[pidx]=sp;

    lfchange=frwins[maxidx*pnum+pidx];
    rhchange=bkwins[maxidx*pnum+pidx];
    //if (sp > thd && sa[maxidx]>0.03)
    //if (sp > thd && sa[maxidx]>0.04 && rhchange >0.2)
    if (sp > thd && sa[maxidx]>0.04 && (lfchange-rhchange)>0.05 && rhchange < 0.18 )
    {
	chtime[pidx]=bandtime[maxidx];
	chscale[pidx]=sa[maxidx];
    }
    else
    {
	chtime[pidx]=0;
    }

    lfwins[pidx]=frwins[maxidx*pnum+pidx];
    rhwins[pidx]=bkwins[maxidx*pnum+pidx];

    delete [] sa;

    return 0;
}

long longtermchange_v2(float* mva, float* spdev, long pidx, long pnum, long tsbands, time_t* bandtime, double* chprb, time_t* chtime, float* chscale)
{

    long i, maxidx;

    double* sa;

    double sp, thd;


    thd = 0.7;
    //thd = 1.2;


    sa = new double[tsbands];

    for(i=0;i<tsbands;i++)
    {
	sa[i]=mva[i*pnum+pidx];
    }

    maxidx = gsl_stats_max_index(sa, 1, tsbands);

    sp = spdev[maxidx*pnum+pidx];

    chprb[pidx]=sp;

    //if (sp > thd && sa[maxidx]>0.03)
    if (sp > thd && sa[maxidx]>0.04)
    {
	chtime[pidx]=bandtime[maxidx];
	chscale[pidx]=sa[maxidx];
    }
    else
    {
	chtime[pidx]=0;
    }

    delete [] sa;

    return 0;
}


long longtermchange(double* bandavg, long pidx, long pnum, long tsbands, long width, char* noisemask, time_t* bandtime, double* chprb, time_t* chtime)
{

    double* sa;
    long* saidx;

    double * dif, *absdif;

    long cc, ss, vpnum, tidx, winnum, maxidx;
    size_t* sts;

    long i, j;

    double mu, sd, lf_sum, rh_sum;

    sa = new double[tsbands];
    saidx = new long[tsbands];
    dif = new double[tsbands];
    absdif = new double[tsbands];
    sts = new size_t[tsbands];


    cc=0;
    for(i=0;i<tsbands;i++)
    {
	if (noisemask[i*pnum+pidx]==0)
	{
	    sa[cc]=bandavg[i*pnum+pidx];
	    saidx[cc]=i;
	    dif[cc]=0;
	    absdif[cc]=0;
	    cc++;
	}
    }
    //cout<<cc<<", "<<tsbands<<endl;

    ss=cc;
    if (ss>width*2)
    {
	cc=0;
	winnum=ss-width*2;
	for(i=ss*0.1;i<ss-width;i++)
	{
	    lf_sum=0;
	    rh_sum=0;
	    for(j=0;j<width;j++)
	    {

		lf_sum+=sa[saidx[i-width+j]];
		rh_sum+=sa[saidx[i+j]];
	    }
	    dif[cc]=(rh_sum-lf_sum)/width;
	    absdif[cc]=fabs((rh_sum-lf_sum)/width);
	    cc++;

	}

	gsl_sort_index(sts, absdif, 1, cc);


	mu=gsl_stats_mean(absdif, 1, cc);
	sd=gsl_stats_sd(absdif, 1, cc);

	maxidx= sts[cc-1];

	chprb[pidx]=absdif[maxidx];

	// map to saidx, as maxidx = 0 is equivalent to idx = width in saidx index

	maxidx += width; 

	// map to original time series index using saidx


	maxidx = saidx[maxidx];


	chtime[pidx]=(bandtime[maxidx-1]+bandtime[maxidx])/2;


    }



    delete [] dif;
    delete [] absdif;

    delete [] sa;
    delete [] saidx;

    return 0;
}

/*
   int getatom(string st, int pos, int len)
   {
   string atom;
   atom=st.substr(pos, len);
//cout<<atoi(atom.c_str())<<" ";;
return atoi(atom.c_str());

}
*/

int getbandtime(string bandnames, int bands, time_t* tsbandtime)
{
    long i, ss;

    int pos;



    string st, onepiece;


    struct tm* timeinfo;
    time_t rawtime, bandtime, gap, timeslice;

    time (&rawtime);
    timeinfo=localtime(&rawtime);

    timeinfo->tm_year=1970-1900;
    timeinfo->tm_mon=0;
    timeinfo->tm_mday=1;
    timeinfo->tm_hour=0;
    timeinfo->tm_min=0;
    timeinfo->tm_sec=0;



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
	timeinfo->tm_hour=1;
	timeinfo->tm_min=0;
	timeinfo->tm_sec=0;

	tsbandtime[i]=mktime(timeinfo);
    }


    return 0;

}

int chtimetodate(time_t* chtime, long pnum, float* dateval)
{
    long i;

    struct tm* timeinfo;
    time_t rawtime;

    int mm;
    double yy, qt;

    for(i=0;i<pnum;i++)
    {
	rawtime = chtime[i];
	if (rawtime>0)
	{
	    timeinfo=localtime(&rawtime);

	    yy = (double) (timeinfo->tm_year +1900 );
	    mm = timeinfo->tm_mon;

	    if (mm>=0 && mm<=2)
	    {
		qt=0.125;
	    }
	    else if (mm>=3 && mm<=5)
	    {
		qt=0.375;
	    }
	    else if (mm>=6 && mm<=8)
	    {
		qt=0.625;
	    }
	    else
	    {
		qt=0.875;
	    }

	    dateval[i]=yy+qt;
	}
	else
	{
	    dateval[i]=0;
	}

    }

    return 0;

}


int calspdev(float* mva, long bidx, long pnum, float* spdev)
{

    long i;

    double* sa;

    double mu, sd;

    sa = new double[pnum];

    for(i=0;i<pnum;i++)
    {
	sa[i] = mva[bidx*pnum+i]; 
    }


    mu = gsl_stats_mean(sa, 1, pnum);
    sd = gsl_stats_sd(sa, 1, pnum);


    //cout<<mu<<", "<<sd<<", "<<bidx<<endl;


    for(i=0;i<pnum;i++)
    {
	if (sd>0)
	{
	    spdev[bidx*pnum+i] = fabs((sa[i]-mu)/sd); 
	}
	else
	{
	    spdev[bidx*pnum+i] = 0;
	}
    }


    delete [] sa;
    return 0;


}

int calevi(int* data, double* evi, long oss)
{

    long i;


    double blue, red, nir, scale;

    double C1, C2, L, G;

    G=2.5;
    C1=6;
    C2=7.5;
    L=1;

    scale=10000;

#pragma omp parallel private(i, blue, red, nir) 
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<oss;i++)
    {

	blue =data[0*oss+i];
	red =data[2*oss+i];
	nir =data[3*oss+i];


	if (blue ==-999 || red ==-999 || nir == -999)
	{
	    evi[i]=-2;
	}
	else
	{
	    blue /= scale;
	    red /=scale;
	    nir /=scale;
	    evi[i]=G*((nir-red)/(nir+C1*red-C2*blue+L));
	}
    }

    return 0;

}

int calmndwi(short* data, double* mndwi, long oss)
{

    long i;


    double green, swir, scale;


    scale=10000;

#pragma omp parallel private(i, green, swir) 
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<oss;i++)
    {

	green =data[1*oss+i];
	swir =data[4*oss+i];


	if ( green ==-999 || swir ==-999)
	{
	    mndwi[i]=-2;
	}
	else
	{
	    green /= scale;
	    swir /=scale;
	    mndwi[i]=(green-swir)/(green+swir);
	}
    }

    return 0;

}

int featurefilter(long pidx, long pnum, long tsbands, char* noisemask, double* features)
{
    double thd, ivd;
    double* sa, *disa;
    char* mask, *newmask;
    long i, j, k;
    long cc, ss, sublen, idx, cutpoint;


    double eur[3];
    int counts[3];


    int lab, jlab, tg;


    ivd=-0.099;

    sa = new double [tsbands];
    disa = new double [tsbands];
    mask = new char[tsbands];
    newmask = new char[tsbands];

    cc=0;
    for(i=0;i<tsbands;i++)
    {
	sa[i]=features[i*pnum+pidx];
	mask[i]=noisemask[i*pnum+pidx];
    }


    for(i=0;i<tsbands;i++)
    {
	lab = (int) mask[i];
	if (lab!=1 && sa[i]>ivd)
	{
	    for(k=0;k<3;k++)
	    {
		eur[k]=0;
		counts[k]=0;
	    }

	    for(j=0;j<tsbands;j++)
	    {
		if (mask[j]!=1 && sa[j]>ivd)  // Invalid 
		{
		    disa[j]=fabs(sa[i]-sa[j]);
		}
	    }

	    for(j=0;j<tsbands;j++)
	    {
		jlab = (int) mask[j];
		if (jlab!=1 && i!=j)
		{
		    if (jlab ==0)
		    {
			tg=0;
		    }
		    else if (jlab==2 || jlab ==3)
		    {
			tg=1;
		    }
		    else
		    {
			tg=2;
		    }
		    eur[tg]+=disa[j];
		    counts[tg]++;
		}

	    }
	    for(k=0;k<3;k++)
	    {
		if (counts[k]!=0)
		{
		    eur[k]/=counts[k];
		}
		else
		{
		    eur[k]=DBL_MAX;
		}
	    }
	    tg = gsl_stats_min_index(eur, 1, 3);

	    newmask[i] = tg*2;

	}

    }

    for(i=0;i<tsbands;i++)
    {
	noisemask[i*pnum+pidx] =  newmask[i];
    }




    delete [] newmask;
    delete [] mask;
    delete [] sa;
    delete [] disa;


}


int dcfilter(long pidx, long pnum, long tsbands, double* bandavg, char* noisemask, double*  dcts)
{
    double thd, ivd;
    double* sa, *disa;
    char* mask, *newmask;
    long i, j, k;
    long cc, ss, sublen, idx, cutpoint;


    double mu[3], std[3], eur[3];


    int lab, jlab, tg;


    ivd=-0.099;

    sa = new double [tsbands];
    mask = new char[tsbands];
    newmask = new char[tsbands];

    cc=0;
    for(i=0;i<tsbands;i++)
    {
	sa[i]=bandavg[i*pnum+pidx];
	mask[i]=noisemask[i*pnum+pidx];
	newmask[i]=noisemask[i*pnum+pidx];
    }

    for(k=0;k<3;k++)
    {
	mu[k]=dcts[(k*4+2)*pnum+pidx];
	std[k]=dcts[(k*4+3)*pnum+pidx];
    }


    for(i=0;i<tsbands;i++)
    {
	lab = (int) mask[i];
	if (lab!=1 && sa[i]>ivd)
	{

	    for(k=0;k<3;k++)
	    {
		eur[k]=fabs(sa[i]-mu[k])/std[k];	
	    }

	    tg = gsl_stats_min_index(eur, 1, 3);

	    if (tg>0)
	    {
		tg++;
	    }
	    newmask[i] = (char)tg;
	}

    }

    for(i=0;i<tsbands;i++)
    {
	noisemask[i*pnum+pidx] =  newmask[i];
    }




    delete [] newmask;
    delete [] mask;
    delete [] sa;


}

int waterfilter(long pidx, long pnum, long tsbands, double* bandavg, char* noisemask, double* mndwi)
{
    double thd, ivd;
    double* sa, *dwi;
    char* mask, *newmask;
    long i, j, k;
    long cc, ss, sublen, idx, cutpoint;


    double mu[3], std[3], eur[3];


    int lab, jlab, tg;


    ivd=-0.099;
    thd = 0.05;


    sa = new double [tsbands];
    dwi = new double [tsbands];
    mask = new char[tsbands];
    newmask = new char[tsbands];

    cc=0;
    for(i=0;i<tsbands;i++)
    {
	sa[i]=bandavg[i*pnum+pidx];
	mask[i]=noisemask[i*pnum+pidx];
	newmask[i]=noisemask[i*pnum+pidx];
	dwi[i]=mndwi[i*pnum+pidx];
    }



    for(i=0;i<tsbands;i++)
    {
	lab = (int) mask[i];
	if (lab==2 && sa[i]>ivd)
	{
	    if (dwi[i]>0 && sa[i]< thd)
	    {
		newmask[i] = 0;
	    }
	}

    }

    for(i=0;i<tsbands;i++)
    {
	noisemask[i*pnum+pidx] =  newmask[i];
    }





    delete [] newmask;
    delete [] mask;
    delete [] sa;
    delete [] dwi;


}


int caldcts(long pidx, long pnum, long tsbands, char* noisemask, double* bandavg, double* dcts)
{
    int ilab, lab, tg;
    double thd, ivd;
    double* sa, *data;
    char* mask;
    long i, j, k;
    long cc, ss;





    ivd=-0.099;

    sa = new double [tsbands];
    data = new double [tsbands];
    mask = new char[tsbands];

    for(i=0;i<tsbands;i++)
    {
	sa[i]=bandavg[i*pnum+pidx];
	mask[i]=noisemask[i*pnum+pidx];
    }


    for (lab=0;lab<4;lab++)
    {
	if (lab==1)
	{
	    continue;
	}

	if(lab>1)
	{
	    tg=lab-1;
	}
	else
	{
	    tg=0;
	}

	cc=0;
	for(i=0;i<tsbands;i++)
	{
	    ilab =  (int) mask[i];
	    if (ilab==lab)
	    {
		data[cc]=sa[i];
		cc++;
	    }
	}
	if (cc>0)
	{
	    dcts[(tg*4+0)*pnum+pidx]=gsl_stats_min(data, 1, cc);
	    dcts[(tg*4+1)*pnum+pidx]=gsl_stats_max(data, 1, cc);
	    dcts[(tg*4+2)*pnum+pidx]=gsl_stats_mean(data, 1, cc);
	    dcts[(tg*4+3)*pnum+pidx]=gsl_stats_sd(data, 1, cc);

	}
    }

    delete [] sa;
    delete [] data;
    delete [] mask;

    return 0;

}


/*
   int waterbodydetect(long pnum, long tsbands, char* noisemask, double* bandavg, time_t* bandtime, char* wtbody)
   {


   double* sa;
   vector<long> saidx;

   long i, j, cc;

   time_t curtime, sttime, endtime, mintime, maxtime, width;
   time_t winsize, daysecs, yearsecs;

   double mu, sd, lf_sum, rh_sum;

   daysecs=60*60*24;
   yearsecs = daysecs * 365;

   sttime = bandtime[0];
   maxtime = bandtime[tsbands-1];

   winsize= 2*yearsecs;


   cc=0;



   do
   {
   endtime=sttime+winsize;

   }while(true);


   windowmean(double* bandavg, long pidx, char* noisemask, long pnum, time_t sttime, size_t endtime, time_t* bandtime, long tsbands)

   }
   */


int spatialfilter_ap(long tsbands,  long irow, long icol, char* noisemask, vector<string>& obandnames)
{

    long i, oss;


    //#pragma omp parallel private(i) 
    //#pragma omp for schedule(dynamic) nowait
    for(i=0;i<tsbands;i++)
    {
	//cout<<obandnames[i]<<endl;
	spatialfilter(i, tsbands,  irow, icol, noisemask);
    }


    return  0;
}



int calbandavg(short* data, double* bandavg, long oss, long otbands)
{

    long i, j;
    double sum;

    bool flag;
    double scale=10000.0;

#pragma omp parallel private(i, j, flag, sum) 
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<oss;i++)
    {
	sum=0;

	flag=false;
	for(j=0;j<otbands;j++)
	{
	    sum+=data[j*oss+i]/scale;
	    if (data[j*oss+i]==-999)
	    {
		flag=true;
		break;
	    }
	}
	if (flag || sum == 0)
	{
	    bandavg[i]=-0.0999;
	}
	else
	{
	    bandavg[i]=sum/otbands;
	}
    }



    return 0;



}

int readonerounddata(string* bandnames, short* data, string dirc, long begyear, long endyear, long otbands, long pt, long tsbands, long blocksize, long pnum)
{

    short* oneblock;
    double* sps;
    long i,j,k,m, yearbands, irow, icol;
    vector<int> items;

    long dap, cc;

    string curdirc, imgfname, spfname;
    ifstream fin;


    cc=0;

    for(k=begyear;k<=endyear;k++)
    {
	curdirc=dirc+'/'+itostr(k);
	spfname=curdirc+"/ts_irow_icol.csv";

	readtxtdata(spfname.c_str(), 0, 0, sps, items, irow, icol);

	yearbands= sps[0];
	delete [] sps;

	oneblock=new short[pnum*yearbands];

	dap=0;
	for(i=0;i<otbands;i++)
	{
	    imgfname=curdirc+"/"+"NBAR_"+bandnames[i]+".img";
	    fin.open(imgfname.c_str(), ios::binary);
	    fin.read( (char*) oneblock, pnum*yearbands*sizeof(short));  

	    for(j=0;j<yearbands;j++)
	    {
		for(m=0;m<blocksize;m++)
		{
		    if (pt+m<pnum)
		    {
			data[cc*blocksize+blocksize*j+m+dap]=oneblock[j*pnum+pt+m];
		    }
		    else
		    {
			data[cc*blocksize+blocksize*j+m+dap]=-999;
		    }
		}
	    }

	    fin.close();

	    dap+=tsbands*blocksize;
	}

	delete [] oneblock;
	cc+=yearbands;

    }



    return 0;

}

int filloutimages(long pnum, long numyears, long numsubs, short* subids, float* stats, float* outimage)
{

    long i, j, sb;
    float val;

    for(i=0;i<numyears;i++)
    {
	for(j=0;j<pnum;j++)
	{
	    sb=subids[j];
	    if (sb>=0)
	    {
		val=stats[i*numsubs+sb];
		outimage[i*pnum+j]=val;
	    }
	}

    }


    return 0;

}

int filloutoneimages(long pnum, long numsubs, short* subids, short* stats, short* outimage)
{

    long i, j, sb;
    float val;

    for(j=0;j<pnum;j++)
    {
	sb=subids[j];
	if (sb>=0)
	{
	    val=stats[sb];
	    outimage[j]=val;
	}
    }

    return 0;

}


int write_short_envi_image(string dirc, string filestem, envihdr& ehd, string des, long pnum, short* outimage)
{

    long i;

    string ofname, ohdrfname;

    ofstream fout;

    vector<string> obandnames;
    
    
    ofname=dirc+"/"+filestem+".img";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) outimage, pnum*sizeof(short));
    fout.close();

    ohdrfname=dirc+"/"+filestem+".hdr";
    obandnames.clear();

    obandnames.push_back(des);

    writeenviheader(ohdrfname, des, ehd.samples, ehd.lines, 1, 2, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, obandnames, ehd.projection_info, ehd.coordinate_system_string);


    return 0;

}



int write_envi_image(string dirc, string filestem, long begyear, long endyear, envihdr& ehd, string des, long pnum, long numyears, float* outimage)
{

    long i;

    string ofname, ohdrfname;

    ofstream fout;

    vector<string> obandnames;
    
    
    ofname=dirc+"/"+filestem+".img";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) outimage, numyears*pnum*sizeof(float));
    fout.close();

    ohdrfname=dirc+"/"+filestem+".hdr";
    obandnames.clear();

    for(i=begyear;i<=endyear;i++)
    {
	obandnames.push_back(itostr(i));
    }

    writeenviheader(ohdrfname, des, ehd.samples, ehd.lines, numyears, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, obandnames, ehd.projection_info, ehd.coordinate_system_string);




    return 0;

}

int change_parameters(char* urbancls, long pnum, long numyears, float* flips)
{
    double ubr, maxubr, cbyear;

    long i, j, k, cc, ss, precls, cls;
    




#pragma omp parallel private(i, j, cc, ss, precls, cls, ubr, maxubr, cbyear) 
#pragma omp for schedule(dynamic) nowait

    for(i=0;i<pnum;i++)
    {
	cc=0;
	ss=0;
	for(j=0;j<numyears;j++)
	{
	    cls=(int)urbancls[j*pnum+i];
	    if (j>0)
	    {
		precls=(int)urbancls[(j-1)*pnum+i];
		if ((cls!=precls))
		{
		    cc++;
		}
	    }
	    if (cls==3)
	    {
		ss++;
	    }
	}
	flips[pnum*0+i]=ss/((float)numyears);
	
	ubr=flips[pnum*0+i];

	if (ubr>=0.1)
	{
	    maxubr=0;
	    for(j=0;j<numyears-1;j++)
	    {
		cc=0;
		for(k=j;k<numyears;k++)
		{
		    if 	(urbancls[k*pnum+i]==3)
		    {
			cc++;
		    }

		}
		ubr = cc/((double)(numyears-j));
		if (ubr>maxubr)
		{
		    maxubr=ubr;
		    cbyear=j;
		}

	    }

	    if (maxubr>0.6)
	    {
		flips[pnum*1+i]=cbyear;
	        flips[pnum*2+i]=maxubr;
	    }
	    else
	    {
		 flips[pnum*1+i]=0;
	         flips[pnum*2+i]=0;
	         flips[pnum*0+i]=0;
	    }

	    
	}
	else
	{
	    flips[pnum*2+i]=0;
	    flips[pnum*1+i]=0;
	    flips[pnum*0+i]=0;
	}

    }



    return 0;


}


int main(int argv, char** argc)
{
    // Read time series for a set of pixels (usually coming from a subset of an image)

    string imgfname, hdrfname, oimgfname, ohdrfname, filestem, oclsimgfname, oclshdrfname, dirc, workdirc, partfile, forestfname, pqafname, shforestfname, ofname;
    string wclsfname, wprbfname, fstem, description, wclshdrname, wprbhdrname, spname, hdrfilestem, yearstr;

    double scale, dta, thod, ivd, rt, sum, me;
    float* pr;

    long i, j, h, k, icol, irow, pp, ons, cc, bands, lookahead, x, y, nt, dr, tsbands, ftbands, obands ;
    long bite, chun, ss, pnum, rounds, ppos, lpos, total, vpnum, wvpnum, wbite, spnum, pt, block, width, ans, wans, fstsize, shfstsize;
    long rowmin, rowmax, colmin, colmax;
    size_t idx; 
    int ns, otbands, pos, begyear, endyear;

    double* sps;


    envihdr ehd; 
    ofstream fout;
    ifstream fin;

    string spfname, csvfname, tsbandnames, curdirc, ifname, subdirc, tgtdirc;



    bool flag, accaflag, fmaskflag, accasdflag, fmasksdflag, contflag;

    unsigned short pqaval;

    vector<int> items;
    vector<string> obandnames;

    ofstream fout_wcls, fout_wprb;
    ifstream* fins;
    ifstream finpqa;

    dta=1.0;
    dirc=argc[1];
    subdirc=argc[2];
    begyear=atoi(argc[3]);
    endyear=atoi(argc[4]);


    tgtdirc=dirc+"/"+subdirc;


    tsbands=0;

    i=begyear;
    curdirc=tgtdirc+'/'+itostr(i);
    spfname=curdirc+"/ts_irow_icol.csv";
    readtxtdata(spfname.c_str(), 0, 0, sps, items, irow, icol);
    irow=sps[1];
    icol=sps[2];

    cout<<"tsbands = "<<sps[0]<<endl;
    cout<<"irow = "<<irow<<endl;
    cout<<"icol = "<<icol<<endl;
    
    delete [] sps;

    long numyears, sb;

    numyears = endyear-begyear+1;
    pnum = irow*icol;

    short* subids;


    subids=new short[pnum];


    ifname=tgtdirc+"/suburbids.img";
    fin.open(ifname.c_str(), ios::binary);
    fin.read((char*) subids, pnum*sizeof(short));
    fin.close();

    int cls;
    int numsubs;
    numsubs=0;
    for(i=0;i<pnum;i++)
    {
	if (subids[i]>numsubs)
	{
	    numsubs=subids[i];
	}
    }

    numsubs++;

    cout<<"Number of suburbs = "<<numsubs<<endl;


    int *subcounts, *devstats;
    float val;

    subcounts=new int[numsubs];

    for(i=0;i<numsubs;i++)
    {
	subcounts[i]=0;
    }
    for(j=0;j<pnum;j++)
    {
	sb=subids[j];
	if (sb>=0)
	{
	    subcounts[sb]++;
	}
    }



    char* urbancls;
    string yearst;

    urbancls= new char[numyears*pnum];

    cc=0;
    for(i=begyear;i<=endyear;i++)
    {
	yearst=itostr(i);
        ifname=tgtdirc+"/"+yearst+"/urban_spec_5c.img";
	fin.open(ifname.c_str(), ios::binary);
        fin.read((char*) &urbancls[cc*pnum], pnum*sizeof(char));
        fin.close();
	cc++;
    }

    /*
    ifname=dirc+"/urban_change.img";
    fin.open(ifname.c_str(), ios::binary);
    fin.read((char*) ubchange, pnum*sizeof(char));
    fin.close();
    */


    curdirc=tgtdirc+"/"+itostr(endyear);
    hdrfname=tgtdirc+"/urban_spec_5c.hdr";
    readhdrfile(hdrfname, ehd);


    float* flips;

    int ofbb, kd;

    ofbb=3;


    flips=new float[pnum*ofbb];
    


    change_parameters(urbancls, pnum, numyears, flips);



    double ubr, maxubr, cbyear;

    for(i=0;i<pnum;i++)
    {
	maxubr=flips[pnum*2+i];

	if (maxubr==1)
	{
	    cbyear=flips[pnum*1+i];
	    if (cbyear>0)
	    {

		for(j=0;j<cbyear;j++)
		{
		    if (urbancls[j*pnum+i]!=0)
		    {
			urbancls[j*pnum+i]=1;
		    }
		}
	    }
	}
	if (flips[pnum*1+i]==0 && flips[pnum*0+i]==0 && flips[pnum*2+i]==0)
	{
	    for(j=0;j<numyears;j++)
	    {
		if (urbancls[j*pnum+i]!=0)
		{
		    urbancls[j*pnum+i]=1;
		}
	    }
	}
	if (maxubr>0.5)
	{   
	    for(j=0;j<numyears;j++)
	    {
		if (urbancls[j*pnum+i]==3)
		{
		    kd=j;
		    break;
		}
	    }
	    for(j=kd;j<numyears;j++)
	    {
		if (urbancls[j*pnum+i]!=0)
		{
		    urbancls[j*pnum+i]=3;
		}
	    }

	}
    }

    ofname=tgtdirc+"/urban_extent_"+subdirc+".img";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) urbancls, numyears*pnum*sizeof(char));
    fout.close();


    ohdrfname=tgtdirc+"/urban_extent_"+subdirc+".hdr";
    obandnames.clear();

    for(i=begyear;i<=endyear;i++)
    {
	yearst=itostr(i);
	obandnames.push_back(yearst);
    }


    writeenviheader(ohdrfname, "landcover classes", ehd.samples, ehd.lines, numyears, 1, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, obandnames, ehd.projection_info, ehd.coordinate_system_string);


    change_parameters(urbancls, pnum, numyears, flips);

    ofname=tgtdirc+"/urban_cd_"+subdirc+".img";
    ohdrfname=tgtdirc+"/urban_cd_"+subdirc+".hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) flips, ofbb*pnum*sizeof(float));
    fout.close();

    obandnames.clear();
    obandnames.push_back("urban ratio in time series");
    obandnames.push_back("Year when urban development commenced");
    obandnames.push_back("urban ratio after development");

    writeenviheader(ohdrfname, "landcover change counts", ehd.samples, ehd.lines, ofbb, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, obandnames, ehd.projection_info, ehd.coordinate_system_string);






    delete [] subids;
    delete [] flips;
    delete [] urbancls;
    delete [] subcounts;

    return 0;

}




