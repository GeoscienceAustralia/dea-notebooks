#include "statsml.h"

using namespace std;


int writescript_urban(string ofname, string tgtdirc, string lat_top, string lat_bottom, string lon_left, string lon_right, string beg_year, string end_year)
{
    string outdirc, yearstr, command;
    
    long i, bb_year, ee_year;    


    bb_year=atoi(beg_year.c_str());
    ee_year=atoi(end_year.c_str());



    ofstream fout;
    fout.open(ofname.c_str(), ios::out);
    fout<<"#!/bin/bash"<<endl;
    fout<<"module use /g/data/v10/public/modules/modulefiles"<<endl;
    fout<<"module load agdc-py3-prod"<<endl;


    for(i=bb_year;i<=ee_year;i++)
    {
	yearstr=itostr(i);
	outdirc=tgtdirc+"/"+yearstr;
		
	command="mkdir "+outdirc;
	system(command.c_str());
	fout<<"python3 /g/data1/u46/pjt554/change_detection/load_landsat_nbart_ts.py ";
	fout<<lat_top<<" ";
	fout<<lat_bottom<<" ";
	fout<<lon_left<<" ";
	fout<<lon_right<<" ";

	fout<<yearstr<<"-01-01 ";
	fout<<yearstr<<"-12-31 ";

	fout<<outdirc;
	fout<<endl;

	
    }


    fout.close();





    return 0;
}

int writescript_tsmask(string ofname, string tgtdirc, string beg_year, string end_year)
{


    ofstream fout;
    fout.open(ofname.c_str(), ios::out);
    fout<<"#!/bin/bash"<<endl;
    fout<<"module load gsl"<<endl;
    fout<<"/g/data1/u46/pjt554/change_detection/tsmask_multiyears ";
    fout<<tgtdirc<<" ";
    fout<<beg_year<<" ";
    fout<<end_year<<" ";
    fout<<"clouds.hdr";
    fout<<endl;


    fout.close();


    return 0;
}


int writescript_indices(string ofname, string tgtdirc, string beg_year, string end_year)
{

    string yearstr;
    long i, bb_year, ee_year;    


    bb_year=atoi(beg_year.c_str());
    ee_year=atoi(end_year.c_str());


    ofstream fout;
    fout.open(ofname.c_str(), ios::out);
    fout<<"#!/bin/bash"<<endl;
    fout<<"module load gsl"<<endl;
    fout<<"export OMP_NUM_THREADS=8"<<endl;
    for(i=bb_year;i<=ee_year;i++)
    {
	yearstr=itostr(i);
	fout<<"/g/data1/u46/pjt554/change_detection/urban ";
	fout<<tgtdirc<<"/"<<yearstr;
	fout<<endl;

    }
    fout.close();


    return 0;
}

int writescript_clusters(string ofname, string tgtdirc, string beg_year, string end_year, int numcls)
{

    string yearstr, sourcehdr;
    long i, bb_year, ee_year;    


    bb_year=atoi(beg_year.c_str());
    ee_year=atoi(end_year.c_str());


    sourcehdr=tgtdirc+"/urban_spec_5c.hdr";


    ofstream fout;
    fout.open(ofname.c_str(), ios::out);
    fout<<"#!/bin/bash"<<endl;
    fout<<"export OMP_NUM_THREADS=8"<<endl;
    fout<<"module use /g/data/v10/public/modules/modulefiles"<<endl;
    fout<<"module load agdc-py3-prod"<<endl;

    for(i=bb_year;i<=ee_year;i++)
    {
	yearstr=itostr(i);
	fout<<"python3 /g/data1/u46/pjt554/change_detection/ana_cluster_raw.py ";
	fout<<tgtdirc<<"/"<<yearstr<<" ";
	fout<<sourcehdr<<" ";
	fout<<numcls<<" ";
	fout<<endl;
    }
    fout.close();


    return 0;
}

int writescript_cleanups(string ofname, string tgtdirc, string beg_year, string end_year)
{

    string yearstr, sourcehdr;
    long i, bb_year, ee_year;    


    bb_year=atoi(beg_year.c_str());
    ee_year=atoi(end_year.c_str());




    ofstream fout;
    fout.open(ofname.c_str(), ios::out);
    fout<<"#!/bin/bash"<<endl;

    for(i=bb_year;i<=ee_year;i++)
    {
	yearstr=itostr(i);
	fout<<"rm ";
	fout<<tgtdirc<<"/"<<yearstr<<"/NBAR_* ";
	fout<<endl;
    }
    fout.close();


    return 0;
}

int writescript_maprawclass(string ofname, string tgtdirc, string beg_year, string end_year, int numcls)
{


    ofstream fout;
    fout.open(ofname.c_str(), ios::out);
    fout<<"#!/bin/bash"<<endl;
    fout<<"module load gsl"<<endl;
    fout<<"/g/data1/u46/pjt554/change_detection/maprawclass ";
    fout<<tgtdirc<<" ";
    fout<<beg_year<<" ";
    fout<<end_year<<" ";
    fout<<numcls<<" ";
    fout<<endl;


    fout.close();


    return 0;
}



int main(int argv, char** argc)
{

    string dirc, subdirc, beg_year, end_year, tgtdirc, curdirc, hdrfname, ohdrfname, comstr, yearstr, ifname, ofname;

   long i, j, k, s, l, numcls, ss;
    long bb_year, ee_year, pnum, cc;    
    envihdr ehd; 

    ifstream fin;
    ofstream fout;

    double thd, rate;


    dirc=argc[1];
    subdirc=argc[2];
    beg_year=argc[3];
    end_year=argc[4];
    thd=atof(argc[5]);

    tgtdirc=dirc+"/"+subdirc;



    bb_year=atoi(beg_year.c_str());
    ee_year=atoi(end_year.c_str());

    hdrfname=tgtdirc+"/"+beg_year+"/urban_spec_5c_raw.hdr";
    readhdrfile(hdrfname, ehd);
    pnum=ehd.samples*ehd.lines;


    int numyears;
    numyears=ee_year-bb_year+1;


    char* rawclass, *beclass;

    int* ffclass;

    rawclass=new char[pnum];
    beclass=new char[pnum];
    ffclass=new int[pnum*numyears];


    cc=0;
    for(i=bb_year;i<=ee_year;i++)
    {
	yearstr=itostr(i);
	curdirc=tgtdirc+"/"+yearstr;



	ifname=curdirc+"/urban_spec_5c.img";
	fin.open(ifname.c_str(), ios::binary);
	if (fin.good())
	{
	    fin.read((char*) rawclass, pnum*sizeof(char));
	    fin.close();

	    for(j=0;j<pnum;j++)
	    {
		ffclass[cc*pnum+j]=(int)rawclass[j];
	    }

	}
	cc++;
    }

    ss=0;
    for(j=0;j<pnum;j++)
    {
	cc=0;
	for(i=0;i<numyears;i++)
	{
	    k=ffclass[i*pnum+j];
	    if (k==1 || k==0)
	    {
		cc++;
	    }
	}
	rate=cc/(double)numyears;
	if (rate<=thd)
	{
	    ss++;
	    for(i=0;i<numyears;i++)
	    {
		ffclass[i*pnum+j]=2;
	    }
	}
    }
    
    cout<<"ss="<<ss<<" out of "<<pnum<<", ratio="<<(ss/(double)pnum)<<endl;
    
    cc=0;
    for(i=bb_year;i<=ee_year;i++)
    {
	yearstr=itostr(i);
	curdirc=tgtdirc+"/"+yearstr;
        ofname=curdirc+"/urban_spec_5c_ff.img";
        ohdrfname=curdirc+"/urban_spec_5c_ff.hdr";
	for(j=0;j<pnum;j++)
	{
	    beclass[j]=(char)ffclass[cc*pnum+j];
	}
	fout.open(ofname.c_str(), ios::binary);
	fout.write((char*) beclass, pnum*sizeof(char));
	fout.close();
	cc++;
	comstr="cp "+hdrfname+" "+ohdrfname;
	system(comstr.c_str());	
    }

    delete [] rawclass;
    delete [] beclass;
    delete [] ffclass;


    return 0;
}
