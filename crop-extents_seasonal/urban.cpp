#include "statsml.h"

using namespace std;

bool getbit(unsigned short val, int bit)
{

    bool flag;
    unsigned short tgt[]={1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32786};

    flag = (bool) (val & tgt[bit]);

    return flag;
}

float NDI_ab(float a, float b)
{
    if ((a==-999) || (b==-999))
    {
	return -999;
    }
    if (a+b !=0)
    {
	return (a-b)/(a+b);
    }
    else
    {
	return -999;
    }
}

float RDI_ab(float a, float b)
{
    if ((a==-999) || (b==-999))
    {
	return -999;
    }
    if (b !=0)
    {
	return a/b;
    }
    else
    {
	return -999;
    }
}

float ADI_ab(float a, float b)
{
    if ((a==-999) || (b==-999))
    {
	return -999;
    }
    return a-b;
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

int spatialinterplore(long bandidx, long numbands, long irow, long icol, long width, float* data)
{



    int offset;

    float ivd = -999;

    long i, j, k, p, x, y, cc, pp, pnum;

    float val, sum;

    long x1, x2, y1, y2; 



    offset=(width-1)/2;

    pnum = irow*icol;

    do
    {
	pp=0;
	for(i=0;i<irow;i++)
	{
	    for(j=0;j<icol;j++)
	    {
		val  = data[bandidx*pnum+i*icol+j];
		if (val==ivd)
		{
		    cc=0;
		    sum=0;
		    x1=i-offset;
		    if (x1<0)
		    {
			x1=0;
		    }
		    x2=x1+width;
		    if (x2>irow)
		    {
			x2=irow;
			x1=x2-width;
		    }
		    y1=j-offset;
		    if (y1<0)
		    {
			y1=0;
		    }
		    y2=y1+width;
		    if (y2>icol)
		    {
			y2=icol;
			y1=y2-width;
		    }




		    for(x=x1;x<x2;x++)
		    {
			for(y=y1;y<y2;y++)
			{

			    if (x!=i || y!=j)
			    {
				val=data[bandidx*pnum+x*icol+y];
				if (val!=ivd)
				{
				    cc++;
				    sum+=val;
				}
			    }
			}
		    }
		    if (cc>5)
		    {
			data[bandidx*pnum+i*icol+j]=sum/cc;
		    }   
		    else
		    {
			pp++;
		    }
		}
	    }

	}

    }while(pp>0);

    return 0;

}






int spatialfilter(long tsidx, long tsbands,  long irow, long icol, float* data, char* noisemask)
{

    char* mask;

    char mc, nlab;

    int newlab;


    long i, j, k, p, x, y, cc, pnum;


    pnum = irow*icol;

    mask = new char[pnum];


    for(i=0;i<pnum;i++)
    {
	mask[i] = noisemask[tsidx*pnum+i];
    }



    for(i=1;i<irow-1;i++)
    {
	for(j=1;j<icol-1;j++)
	{
	    mc  = mask[i*icol+j];
	    if (mc>0)
	    {
		mc=1;
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
			nlab=noisemask[tsidx*pnum+x*icol+y];
			if (nlab>0)
			{
			    newlab+=nlab;
			    nlab=1;
			}
			if (mc!=nlab)
			{
			    cc++;
			}
		    }
		}
	    }
	    if (cc>6)
	    {
		if (mc>0)
		{
		    mask[i*icol+j]=0;
		}
		else
		{
		    newlab=newlab/cc;
		    mask[i*icol+j]=(char)newlab;
		}

	    }   
	}
    }


    for(i=0;i<pnum;i++)
    {
	noisemask[tsidx*pnum+i] = mask[i];
    }





    delete [] mask;

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

	    findnoise(sa, saidx, cc, cc*0.2, cc*0.8, 5, mask);


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



    findnoise(sa, saidx, cc, cc*0.3, cc*0.8, 2, mask);


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

    findnoise(sa, saidx, cc, cc*0.3, cc*0.9, 2, mask);



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
	    kNNnoisefilter(i, mask, sa, bandtime[i], width, bandtime, tsbands, N, 3);
	}
    }

    N=5;

    for(i=0;i<tsbands;i++)
    {
	if (mask[i]==0)
	{
	    kNNnoisefilter(i, mask, sa, bandtime[i], width, bandtime, tsbands, N, 3);
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
	findnoise(sa, saidx, cc, cc*0.1, cc*0.85, 6, mask);
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
	    kNNnoisefilter(i, mask, sa, bandtime[i], 10*width, bandtime, tsbands, N, 7);
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
	    kNNnoisefilter(i, mask, sa, bandtime[i], 10*width, bandtime, tsbands, N, 7);
	}
    }

    N=5;

    for(i=0;i<tsbands;i++)
    {
	if (mask[i]==0 && sa[i]<0.09)
	{
	    kNNnoisefilter(i, mask, sa, bandtime[i], 10*width, bandtime, tsbands, N, 7);
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
    double sum;

    ss = saidx.size();

    if (ss>10)
    {
	cc=0;
	sum=0;
	for(i=0;i<ss;i++)
	{
	    idx=saidx[i];
	    if (noisemask[idx*pnum+pidx]==0 && bandavg[idx*pnum+pidx] > -1)
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


long calchange_v4(double* bandavg, long pidx, long pnum, long tsbands, time_t width, char* noisemask, time_t* bandtime, float* mva, float* frwins, float* bkwins, double* evi, float* mvevi)
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

	/*
	   if (pidx==0)
	   {
	   cout<<mintime<<", "<<maxtime<<", "<<i<<", left, "<<sttime<<", "<<endtime<<endl;
	   }
	   */

	if (sttime>=mintime)
	{
	    lf_sum = windowmean(evi, pidx, noisemask, pnum, sttime, endtime, bandtime, tsbands);
	}
	else
	{
	    lf_sum=0;
	}


	sttime = curtime;
	endtime = curtime + width;


	/*
	   if (pidx==0)
	   {
	   cout<<mintime<<", "<<maxtime<<", "<<tsbands-i<<", right, "<<sttime<<", "<<endtime<<endl;
	   }
	   */

	if (endtime<maxtime)
	{
	    rh_sum = windowmean(evi, pidx, noisemask, pnum, sttime, endtime, bandtime, tsbands);
	}
	else
	{
	    rh_sum=0;
	}

	if (lf_sum==0 || rh_sum ==0)
	{
	    frwins[i*pnum+pidx]=0;
	    bkwins[i*pnum+pidx]=0;
	    mvevi[i*pnum+pidx]=0;
	}
	else
	{
	    frwins[i*pnum+pidx]= lf_sum;
	    bkwins[i*pnum+pidx]= rh_sum;
	    mvevi[i*pnum+pidx]= lf_sum - rh_sum;
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



long longtermchange_v4(float* mvevi, float* mva, float* frwins, float* bkwins, float* spdev, long pidx, long pnum, long tsbands, time_t* bandtime, double* chprb, time_t* chtime, float* chscale, float* lfwins, float* rhwins, float* maxmva, double albthd, double mvethd, double rhethd)
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
	sa[i]=mva[i*pnum+pidx]+mvevi[i*pnum+pidx];
    }

    maxidx = gsl_stats_max_index(sa, 1, tsbands);

    sp = spdev[maxidx*pnum+pidx];

    chprb[pidx]=sp;

    lfchange=frwins[maxidx*pnum+pidx];
    rhchange=bkwins[maxidx*pnum+pidx];

    //if (sp > thd && sa[maxidx]>0.04 && (lfchange-rhchange)>0.05 && rhchange < 0.18 )
    //if (mva[maxidx*pnum+pidx]>0.04 && mvevi[maxidx*pnum+pidx]>0.05 && rhchange < 0.18 )
    if (mva[maxidx*pnum+pidx]>albthd && mvevi[maxidx*pnum+pidx]>mvethd && rhchange < rhethd)
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
    maxmva[pidx]=mva[maxidx*pnum+pidx];

    delete [] sa;

    return 0;
}

long longtermchange_v3(float* mva, float* frwins, float* bkwins, float* spdev, long pidx, long pnum, long tsbands, time_t* bandtime, double* chprb, time_t* chtime, float* chscale, float* lfwins, float* rhwins, float* maxmva)
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

    //if (sp > thd && sa[maxidx]>0.04 && (lfchange-rhchange)>0.05 && rhchange < 0.18 )
    if (sa[maxidx]>0.04 && (lfchange-rhchange)>0.05 && rhchange < 0.18 )
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
    maxmva[pidx]=mva[maxidx*pnum+pidx];

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


	if ( (blue ==-999) || (red ==-999) || (nir == -999) )
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

int calndvi(int* data, double* evi, long oss)
{

    long i;


    double blue, red, nir, scale;



#pragma omp parallel private(i, blue, red, nir) 
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<oss;i++)
    {

	blue =data[0*oss+i];
	red =data[2*oss+i];
	nir =data[3*oss+i];


	if ( (blue ==-999) || (red ==-999) || (nir == -999))
	{
	    evi[i]=-2;
	}
	else
	{
	    evi[i]=(nir-red)/(nir+red);
	}
    }

    return 0;

}


// bri  

int caltasseled(short* data, float* bri, float* gre, float* wet, float* ndvi, float* evi, float* savi, float* msavi, float* ndmi, float*  mndwi, long oss, char* noisemask)

{

    long i;


    double blue, green, red, nir, swir1, swir2, scale;
    double sblue, sgreen, sred, snir, sswir1, sswir2;
    

    double C1, C2, L, G;

    G=2.5;
    C1=6;
    C2=7.5;
    L=1;


    scale=10000;

#pragma omp parallel private(i, blue, green, red, nir, swir1, swir2, sblue, sgreen, sred, snir, sswir1, sswir2 ) 
#pragma omp for schedule(dynamic) nowait



    for(i=0;i<oss;i++)
    {

	blue =data[0*oss+i];
	green =data[1*oss+i];
	red =data[2*oss+i];
	nir =data[3*oss+i];
	swir1 =data[4*oss+i];
	swir2 =data[5*oss+i];

	sblue = blue/scale;
	sgreen = green/scale;
	sred = red/scale;
	snir = nir/scale;
	sswir1 = swir1/scale;
	sswir2 = swir2/scale;


	/*
	   cout<<blue<<", ";
	   cout<<green<<", ";
	   cout<<red<<", ";
	   cout<<nir<<", ";
	   cout<<swir1<<", ";
	   cout<<swir2<<", ";
	   cout<<endl;
	   */

	if ( (blue == -999) || (green == -999) || (red == -999) || (nir == -999) || (swir1 == -999) || (swir2 == -999) )
	{

	    bri[i]=-999;
	//    gre[i]=-999;
	//    wet[i]=-999;
	//    ndvi[i]=-999;
	//    evi[i]=-999;
	//    savi[i]=-999;
	    msavi[i]=-999;
	//    ndmi[i]=-999;
	    mndwi[i]=-999;

	}
	else
	{
	    if (noisemask[i]==0)
	    {
		bri[i]=  0.3037*blue + 0.2793*green + 0.4743*red + 0.5585*nir + 0.5082*swir1 + 0.1863*swir2;
	//	gre[i]= -0.2848*blue - 0.2435*green - 0.5436*red + 0.7243*nir + 0.0840*swir1 - 0.1800*swir2;
	//	wet[i]=  0.1509*blue + 0.1973*green + 0.3279*red + 0.3406*nir - 0.7112*swir1 - 0.4572*swir2;

		bri[i]/=scale;
	//	gre[i]/=scale;
	//	wet[i]/=scale;
		
	//	ndvi[i]=(nir-red)/(nir+red);
	//	evi[i]=G*((snir-sred)/(snir+C1*sred-C2*sblue+L));
	//	savi[i]=((snir-sred)/(snir+sred+0.5))*1.5;
		msavi[i]=(2*snir+1-sqrt((2*snir+1)*(2*snir+1)-8*(snir-sred)))/2;
	//	ndmi[i]=(nir-swir1)/(nir+swir1);
		mndwi[i]=(green-swir1)/(green+swir1);


	    }
	    else
	    {
		bri[i]=-999;
	//	gre[i]=-999;
	//	wet[i]=-999;

	//	ndvi[i]=-999;
	//	evi[i]=-999;
	//	savi[i]=-999;
		msavi[i]=-999;
	//	ndmi[i]=-999;
		mndwi[i]=-999;
	    }


	}

	/*
	   cout<<bri[i]<<", ";
	   cout<<gre[i]<<", ";
	   cout<<wet[i]<<", ";
	   cout<<endl;

*/
    }





    return 0;

}

int findphy(time_t* tsbandtime, long tsbands, long& begpt, long& endpt, long& rbegyear, long& years, long*& phymaps)
{

    long i;
    time_t curtime, begtime, endtime;
    struct tm* timeinfo;
    int month, begyear, endyear;
    bool flag;

    flag=false;

    for(i=0;i<tsbands;i++)
    {
	curtime = tsbandtime[i];
	timeinfo = localtime(&curtime);	
	month=timeinfo->tm_mon+1;	
	if (month==1 || month==2 || month==3)
	{
	    begpt=i;
	    begyear=timeinfo->tm_year+1900;
	    timeinfo->tm_mon=0;
	    timeinfo->tm_mday=1;
	    timeinfo->tm_hour=0;
	    timeinfo->tm_min=0;
	    timeinfo->tm_sec=1;
	    begtime = mktime(timeinfo);
	    flag=true;
	    break;
	}
    }

    if (!flag) // not found, put the first point as beginning
    {
	i=0;
	curtime = tsbandtime[i];
	timeinfo = localtime(&curtime);	
	begpt=i;
	begyear=timeinfo->tm_year+1900;
	timeinfo->tm_mon=0;
	timeinfo->tm_mday=1;
	timeinfo->tm_hour=0;
	timeinfo->tm_min=0;
	timeinfo->tm_sec=1;
	begtime = mktime(timeinfo);
    }





    cout<<"begtime="<<asctime(timeinfo)<<endl;


    flag=false;
    for(i=tsbands-1;i>=0;i--)
    {
	curtime = tsbandtime[i];
	timeinfo = localtime(&curtime);	
	month=timeinfo->tm_mon+1;	
	if (month==12 || month==11 || month==10)
	{
	    endpt=i;
	    curtime = tsbandtime[i];
	    timeinfo = localtime(&curtime);	
	    endyear=timeinfo->tm_year+1900;
	    timeinfo->tm_mon=11;
	    timeinfo->tm_mday=31;
	    timeinfo->tm_hour=23;
	    timeinfo->tm_min=59;
	    timeinfo->tm_sec=59;
	    endtime = mktime(timeinfo);
	    break;
	}

    }

    if (!flag)
    {
	i=tsbands-1;
	endpt=i;
	endyear=timeinfo->tm_year+1900;
	timeinfo->tm_mon=11;
	timeinfo->tm_mday=31;
	timeinfo->tm_hour=23;
	timeinfo->tm_min=59;
	timeinfo->tm_sec=59;
	endtime = mktime(timeinfo);
    }


    cout<<"endtime="<<asctime(timeinfo)<<endl;

    years= endyear-begyear+1;



    long oss;
    time_t gap;

    oss=years*4;
    phymaps = new long[tsbands];


    gap = (endtime-begtime)/oss;

    for(i=0;i<tsbands;i++)
    {
	if (i<begpt || i>endpt)
	{
	    phymaps[i]=-1;
	}
	else
	{
	    phymaps[i] = (tsbandtime[i]-begtime)/gap;
	}
	//cout<<"i="<<i<<", maps="<<phymaps[i]<<endl;
    }

    rbegyear=begyear;

    return 0;


}


int calphyindexes(float* data, long idx, long years, long pnum, long tsbands, long begpt, long endpt, long begyear, long* phymaps, char* noisemask, float* phydata )
{

    long i, j, map, cc;
    float val;

    string st;
    int mask;

    long * cct;
    float *raw;

    double sum;

    cct=new long[years*4];
    raw=new float[years*4];


    for(i=0;i<years*4;i++)
    {
	cct[i]=0;
	raw[i]=0;
    }


    cc=0;
    sum=0;
    for(i=begpt;i<=endpt;i++)
    {
	val = data[pnum*i+idx];
	mask = (int) noisemask[pnum*i+idx];
	map = phymaps[i];

	if (mask==0 && map>=0 && val>-999)
	{
	    raw[map]+=val;      
	    cct[map]++;      
	    sum+=val;
	    cc++;
	}
    }

    for(i=0;i<years*4;i++)
    {
	if (cct[i]>0)
	{
	    raw[i]/=cct[i];
	}
	else
	{
	    raw[i]=-999;
	}
    }

    for(i=0;i<years;i++)
    {
	for(j=0;j<4;j++)
	{
	    phydata[i*pnum*16+j*pnum+idx]=raw[i*4+j];
	}
	phydata[i*pnum*16+4*pnum+idx] = NDI_ab(raw[i*4+0], raw[i*4+1]);
	phydata[i*pnum*16+5*pnum+idx] = NDI_ab(raw[i*4+0], raw[i*4+2]);
	phydata[i*pnum*16+6*pnum+idx] = NDI_ab(raw[i*4+0], raw[i*4+3]);
	phydata[i*pnum*16+7*pnum+idx] = NDI_ab(raw[i*4+1], raw[i*4+2]);
	phydata[i*pnum*16+8*pnum+idx] = NDI_ab(raw[i*4+1], raw[i*4+3]);
	phydata[i*pnum*16+9*pnum+idx] = NDI_ab(raw[i*4+2], raw[i*4+3]);


	phydata[i*pnum*16+10*pnum+idx] = ADI_ab(raw[i*4+0], raw[i*4+1]);
	phydata[i*pnum*16+11*pnum+idx] = ADI_ab(raw[i*4+0], raw[i*4+2]);
	phydata[i*pnum*16+12*pnum+idx] = ADI_ab(raw[i*4+0], raw[i*4+3]);
	phydata[i*pnum*16+13*pnum+idx] = ADI_ab(raw[i*4+1], raw[i*4+2]);
	phydata[i*pnum*16+14*pnum+idx] = ADI_ab(raw[i*4+1], raw[i*4+3]);
	phydata[i*pnum*16+15*pnum+idx] = ADI_ab(raw[i*4+2], raw[i*4+3]);
	
	if (cc>0)
	{
	    phydata[i*pnum*16+4*pnum+idx]=sum/cc;
	}
	else
	{
	    phydata[i*pnum*16+4*pnum+idx]=-999;
	}
    }

      return 0;
}



int getphybandnames(vector<string>& phybandnames, int begyear, int years)
{


    long i, j;
    
    string st;

   phybandnames.clear();


    for(i=0;i<years;i++)
    {
	for(j=0;j<4;j++)
	{
	    st=itostr(i+begyear)+"S"+itostr(j+1);
	    phybandnames.push_back(st);
	}
	st=itostr(i+begyear);
	phybandnames.push_back(st+"NR_S1S2");
	phybandnames.push_back(st+"NR_S1S3");
	phybandnames.push_back(st+"NR_S1S4");
	phybandnames.push_back(st+"NR_S2S3");
	phybandnames.push_back(st+"NR_S2S4");
	phybandnames.push_back(st+"NR_S3S4");
	phybandnames.push_back(st+"AR_S1S2");
	phybandnames.push_back(st+"AR_S1S3");
	phybandnames.push_back(st+"AR_S1S4");
	phybandnames.push_back(st+"AR_S2S3");
	phybandnames.push_back(st+"AR_S2S4");
	phybandnames.push_back(st+"AR_S3S4");

    }
    
    return 0;

}


int main(int argv, char** argc)
{
    // Read time series for a set of pixels (usually coming from a subset of an image)

    string imgfname, hdrfname, oimgfname, ohdrfname, filestem, oclsimgfname, oclshdrfname, dirc, workdirc, partfile, forestfname, pqafname, shforestfname, ofname;
    string wclsfname, wprbfname, fstem, description, wclshdrname, wprbhdrname, spname, hdrfilestem, yearstr, maskfname;

    double scale, dta, thod, ivd, rt, sum, me;
    float* pr;

    long i, j, h, k, icol, irow, pp, ons, cc, bands, lookahead, x, y, nt, dr, tsbands, ftbands, obands ;
    long bite, chun, ss, pnum, rounds, ppos, lpos, total, vpnum, wvpnum, wbite, spnum, pt, block, width, ans, wans, fstsize, shfstsize;
    long rowmin, rowmax, colmin, colmax;
    size_t idx; 
    int ns, otbands, pos;



    envihdr ehd; 
    ofstream fout;
    ifstream fin;

    string spfname, csvfname, tsbandnames;
    time_t * tsbandtime;



    bool flag, accaflag, fmaskflag, accasdflag, fmasksdflag, contflag;

    unsigned short pqaval;

    vector<int> items;

    double albthd, mvethd, rhethd;
    ofstream fout_wcls, fout_wprb;
    ifstream* fins;
    ifstream finpqa;

    dta=1.0;
    dirc=argc[1];



    string bandnames[]={"blue", "green", "red", "nir", "swir1", "swir2"};



    hdrfname=dirc+"/NBAR_blue.hdr";
    readhdrfile(hdrfname, ehd);
    tsbandnames=ehd.band_names;



    ivd=-999;
    ans=10;
    wans=7;
    otbands=6;
    ftbands=21;

    double* sps;
    short* oneblock;
    short* data;

    char *noisemask;
    float *clsrate;

    unsigned short paqval;


    vector<string> obandnames;
    vector<string> phybandnames;

    scale=10000;
    long brow, bcol, oss;

    //spfname=dirc+"/"+filestem+"_ts_irow_icol.csv";
    spfname=dirc+"/ts_irow_icol.csv";
    //pqafname=dirc+"/"+filestem+"_PQA_mask.csv";


    readtxtdata(spfname.c_str(), 0, 0, sps, items, irow, icol);

    tsbands = sps[0];
    irow=sps[1];
    icol=sps[2];

    cout<<"tsbands = "<<tsbands<<endl;
    cout<<"irow = "<<irow<<endl;
    cout<<"icol = "<<icol<<endl;

    tsbandtime = new time_t[tsbands]; // number of time series bands

    getbandtime(tsbandnames, tsbands, tsbandtime); // Get time stamps (in time_t) of each time series point, save them in tsbandtime 


    pnum = irow*icol;
    oss = tsbands*pnum;

    data=new short[otbands*oss];
    noisemask= new char[oss];
    oneblock = new short[oss];

    pt=0;
    for(i=0;i<otbands;i++)
    {
	imgfname=dirc+"/"+"NBAR_"+bandnames[i]+".img";
	fin.open(imgfname.c_str(), ios::binary);
	fin.read( (char*) oneblock, oss*sizeof(short));  

	for(j=0;j<oss;j++)
	{
	    data[j+pt]=oneblock[j];
	}
	fin.close();
	pt+=oss;
    }

    delete [] oneblock;
    delete [] sps;


    maskfname=dirc+"/tsmask.img";
    fin.open(maskfname.c_str(), ios::binary);
    fin.read( (char*) noisemask, oss*sizeof(char));  
    fin.close();





    long years, begpt, endpt, begyear;
    long* phymaps;


    float *bri, *gre, *wet, *ndvi, *evi, *savi, *msavi, *ndmi, *mndwi;

    bri = new float[oss];
//    gre = new float[oss];
//    wet = new float[oss];
//    ndvi= new float[oss];
//    evi = new float[oss];
//    savi = new float[oss];
    msavi = new float[oss];
//    ndmi = new float[oss];
    mndwi = new float[oss];




    caltasseled(data, bri, gre, wet, ndvi, evi, savi, msavi, ndmi, mndwi, oss, noisemask);

    delete [] data;

    findphy(tsbandtime, tsbands, begpt, endpt, begyear, years, phymaps);

    cout<<"years="<<years<<endl;

    obands=1;


    float *phybri, *phygre, *phywet, *phyndvi, *phyevi, *physavi, *phymsavi, *phyndmi, *phymndwi;


    phybri = new float[pnum*years*16];
    phygre = new float[pnum*years*16];
    phywet = new float[pnum*years*16];
    phyndvi = new float[pnum*years*16];
    phyevi = new float[pnum*years*16];
    physavi = new float[pnum*years*16];
    phymsavi = new float[pnum*years*16];
    phyndmi = new float[pnum*years*16];
    phymndwi = new float[pnum*years*16];


    getphybandnames(phybandnames, begyear, years);

#pragma omp parallel private(i ) 
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<pnum;i++)
    {
	calphyindexes(bri, i, years, pnum, tsbands, begpt, endpt, begyear, phymaps, noisemask, phybri); 
//	calphyindexes(gre, i, years, pnum, tsbands, begpt, endpt, begyear, phymaps, noisemask, phygre); 
//	calphyindexes(wet, i, years, pnum, tsbands, begpt, endpt, begyear, phymaps, noisemask, phywet); 
//	calphyindexes(ndvi, i, years, pnum, tsbands, begpt, endpt, begyear, phymaps, noisemask, phyndvi); 
//	calphyindexes(evi, i, years, pnum, tsbands, begpt, endpt, begyear, phymaps, noisemask, phyevi); 
//	calphyindexes(savi, i, years, pnum, tsbands, begpt, endpt, begyear, phymaps, noisemask, physavi); 
	calphyindexes(msavi, i, years, pnum, tsbands, begpt, endpt, begyear, phymaps, noisemask, phymsavi); 
//	calphyindexes(ndmi, i, years, pnum, tsbands, begpt, endpt, begyear, phymaps, noisemask, phyndmi); 
	calphyindexes(mndwi, i, years, pnum, tsbands, begpt, endpt, begyear, phymaps, noisemask, phymndwi); 

    }

#pragma omp parallel private(i ) 
#pragma omp for schedule(dynamic) nowait
    for(i=0;i<years*16;i++)
    {
	spatialinterplore(i, years*16, irow, icol, 5, phybri);
//	spatialinterplore(i, years*16, irow, icol, 5, phygre);
//	spatialinterplore(i, years*16, irow, icol, 5, phywet);
//	spatialinterplore(i, years*16, irow, icol, 5, phyndvi);
//	spatialinterplore(i, years*16, irow, icol, 5, phyevi);
//	spatialinterplore(i, years*16, irow, icol, 5, physavi);
	spatialinterplore(i, years*16, irow, icol, 5, phymsavi);
//	spatialinterplore(i, years*16, irow, icol, 5, phyndmi);
	spatialinterplore(i, years*16, irow, icol, 5, phymndwi);
    }


    ofname=dirc+"/brightness.img";
    ohdrfname=dirc+"/brightness.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) bri, tsbands*pnum*sizeof(float));
    fout.close();
    obandnames.clear();
    sepbandnames(tsbandnames, tsbands, obandnames);
    writeenviheader(ohdrfname, "Tasselled cap transformation - brightness", ehd.samples, ehd.lines, tsbands, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, obandnames, ehd.projection_info, ehd.coordinate_system_string);

    ofname=dirc+"/msavi.img";
    ohdrfname=dirc+"/msavi.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) msavi, tsbands*pnum*sizeof(float));
    fout.close();
    obandnames.clear();
    sepbandnames(tsbandnames, tsbands, obandnames);
    writeenviheader(ohdrfname, "Modified soil adjusted vegetation index ", ehd.samples, ehd.lines, tsbands, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, obandnames, ehd.projection_info, ehd.coordinate_system_string);

    ofname=dirc+"/mndwi.img";
    ohdrfname=dirc+"/mndwi.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) mndwi, tsbands*pnum*sizeof(float));
    fout.close();
    obandnames.clear();
    sepbandnames(tsbandnames, tsbands, obandnames);
    writeenviheader(ohdrfname, "Modified normalised difference water index", ehd.samples, ehd.lines, tsbands, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, obandnames, ehd.projection_info, ehd.coordinate_system_string);


    int numphyband;


    numphyband = years*16;


    cout<<"tsband="<<tsbands<<endl;

    ofname=dirc+"/phg_bri.img";
    ohdrfname=dirc+"/phg_bri.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) phybri, numphyband*pnum*sizeof(float));
    fout.close();
    writeenviheader(ohdrfname, "Phenology information brightness", ehd.samples, ehd.lines, numphyband, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, phybandnames, ehd.projection_info, ehd.coordinate_system_string);
/*
    ofname=dirc+"/phg_gre.img";
    ohdrfname=dirc+"/phg_gre.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) phygre, numphyband*pnum*sizeof(float));
    fout.close();
    writeenviheader(ohdrfname, "Phenology information greenness", ehd.samples, ehd.lines, numphyband, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, phybandnames, ehd.projection_info, ehd.coordinate_system_string);

    ofname=dirc+"/phg_wet.img";
    ohdrfname=dirc+"/phg_wet.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) phywet, numphyband*pnum*sizeof(float));
    fout.close();
    writeenviheader(ohdrfname, "Phenology information wetness", ehd.samples, ehd.lines, numphyband, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, phybandnames, ehd.projection_info, ehd.coordinate_system_string);


    ofname=dirc+"/phg_ndvi.img";
    ohdrfname=dirc+"/phg_ndvi.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) phyndvi, numphyband*pnum*sizeof(float));
    fout.close();
    writeenviheader(ohdrfname, "Phenology information ndvi", ehd.samples, ehd.lines, numphyband, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, phybandnames, ehd.projection_info, ehd.coordinate_system_string);



 ofname=dirc+"/phg_evi.img";
    ohdrfname=dirc+"/phg_evi.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) phyevi, numphyband*pnum*sizeof(float));
    fout.close();
    writeenviheader(ohdrfname, "Phenology information evi", ehd.samples, ehd.lines, numphyband, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, phybandnames, ehd.projection_info, ehd.coordinate_system_string);



 ofname=dirc+"/phg_savi.img";
    ohdrfname=dirc+"/phg_savi.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) physavi, numphyband*pnum*sizeof(float));
    fout.close();
    writeenviheader(ohdrfname, "Phenology information savi", ehd.samples, ehd.lines, numphyband, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, phybandnames, ehd.projection_info, ehd.coordinate_system_string);

    */


 ofname=dirc+"/phg_msavi.img";
    ohdrfname=dirc+"/phg_msavi.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) phymsavi, numphyband*pnum*sizeof(float));
    fout.close();
    writeenviheader(ohdrfname, "Phenology information msavi", ehd.samples, ehd.lines, numphyband, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, phybandnames, ehd.projection_info, ehd.coordinate_system_string);

/*

 ofname=dirc+"/phg_ndmi.img";
    ohdrfname=dirc+"/phg_ndmi.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) phyndmi, numphyband*pnum*sizeof(float));
    fout.close();
    writeenviheader(ohdrfname, "Phenology information ndmi", ehd.samples, ehd.lines, numphyband, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, phybandnames, ehd.projection_info, ehd.coordinate_system_string);

*/

 ofname=dirc+"/phg_mndwi.img";
    ohdrfname=dirc+"/phg_mndwi.hdr";
    fout.open(ofname.c_str(), ios::binary);
    fout.write((char*) phymndwi, numphyband*pnum*sizeof(float));
    fout.close();
    writeenviheader(ohdrfname, "Phenology information mndwi", ehd.samples, ehd.lines, numphyband, 4, ehd.interleave, ehd.xstart, ehd.ystart, ehd.map_info,  ehd.wavelength_units, phybandnames, ehd.projection_info, ehd.coordinate_system_string);





    delete [] noisemask;
    delete [] tsbandtime;
    delete [] bri;
//    delete [] gre;
//    delete [] wet;
//    delete [] ndvi;
//    delete [] evi;
//    delete [] savi;
    delete [] msavi;
//    delete [] ndmi;

    delete [] phybri;
//    delete [] phygre;
//    delete [] phywet;
//    delete [] phyndvi;
//    delete [] phyevi;
//    delete [] physavi;
    delete [] phymsavi;
//    delete [] phyndmi;
    delete [] phymndwi;
 
    
    
    
    
    delete [] phymaps;




    return 0;
}

