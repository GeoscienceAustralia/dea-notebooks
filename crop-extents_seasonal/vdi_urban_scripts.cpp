#include "comm.h"

using namespace std;


int writescript_urban(string exedirc, string ofname, string tgtdirc, string lat_top, string lat_bottom, string lon_left, string lon_right, string beg_year, string end_year)
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
    fout<<"export OMP_NUM_THREADS=8"<<endl;


    for(i=bb_year;i<=ee_year;i++)
    {
	yearstr=itostr(i);
	outdirc=tgtdirc+"/"+yearstr;
		
	command="mkdir "+outdirc;
	system(command.c_str());
	fout<<"python3 "<<exedirc<<"/load_landsat_nbart_ts.py ";
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

int writescript_tsmask(string exedirc, string ofname, string tgtdirc, string beg_year, string end_year)
{


    ofstream fout;
    fout.open(ofname.c_str(), ios::out);
    fout<<"#!/bin/bash"<<endl;
    fout<<"module load gsl"<<endl;
    fout<<"export OMP_NUM_THREADS=8"<<endl;
    fout<<exedirc<<"/tsmask_multiyears ";
    fout<<tgtdirc<<" ";
    fout<<beg_year<<" ";
    fout<<end_year<<" ";
    fout<<"clouds.hdr";
    fout<<endl;


    fout.close();


    return 0;
}


int writescript_indices(string exedirc, string ofname, string tgtdirc, string beg_year, string end_year)
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
	fout<<exedirc<<"/urban ";
	fout<<tgtdirc<<"/"<<yearstr;
	fout<<endl;

    }
    fout.close();


    return 0;
}

int writescript_clusters(string exedirc, string ofname, string tgtdirc, string beg_year, string end_year, int numcls)
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
	fout<<"python3 "<<exedirc<<"/ana_cluster_raw.py ";
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

int writescript_maprawclass(string exedirc, string ofname, string dirc, string subdirc, string beg_year, string end_year, int numcls)
{

    int j;

    ofstream fout;
    fout.open(ofname.c_str(), ios::out);
    fout<<"#!/bin/bash"<<endl;
    fout<<"module load gsl"<<endl;
    fout<<exedirc<<"/maprawclass ";
    fout<<dirc<<" ";
    fout<<subdirc<<" ";
    fout<<beg_year<<" ";
    fout<<end_year<<" ";
    fout<<numcls<<" 0 ";
    
    for(j=1;j<numcls;j++)
    {
	if (j<numcls-2)
	{
	    fout<<"1 ";
	}
	else
	{
	    fout<<"3 ";
	}
    }


    fout<<endl;


    fout.close();


    return 0;
}

int writescript_detection(string exedirc, string ofname, string dirc, string subdirc, string beg_year, string end_year)
{


    ofstream fout;
    fout.open(ofname.c_str(), ios::out);
    fout<<"#!/bin/bash"<<endl;
    fout<<"module load gsl"<<endl;
    fout<<"export OMP_NUM_THREADS=8"<<endl;
    fout<<exedirc<<"/suburbchange ";
    fout<<dirc<<" ";
    fout<<subdirc<<" ";
    fout<<beg_year<<" ";
    fout<<end_year<<" ";
    fout<<endl;


    fout.close();


    return 0;
}


int writescript_run_all(string ofname, string dirc, string subdirc)
{

    string tgtdirc;

    ofstream fout;
    fout.open(ofname.c_str(), ios::out);
    fout<<"#!/bin/bash"<<endl;
    fout<<"module load gsl"<<endl;


    tgtdirc=dirc+"/"+subdirc;

    ofname=tgtdirc+"/load_landsat_data_"+subdirc+".sh";
    fout<<ofname<<endl;


    ofname=tgtdirc+"/create_tsmask_"+subdirc+".sh";
    fout<<ofname<<endl;


    ofname=tgtdirc+"/create_indices_"+subdirc+".sh";
    fout<<ofname<<endl;


    ofname=tgtdirc+"/create_clusters_"+subdirc+".sh";
    fout<<ofname<<endl;


    ofname=tgtdirc+"/map_raw_class_"+subdirc+".sh";
    fout<<ofname<<endl;



    ofname=tgtdirc+"/urban_change_"+subdirc+".sh";
    fout<<ofname<<endl;

    
    fout.close();
    return 0;
}




int main(int argv, char** argc)
{

    string dirc, subdirc, lat_top, lat_bottom, lon_left, lon_right, beg_year, end_year, ofname, tgtdirc, command, exedirc;
    string shforestname, jobdirc;

    int i, s, l, numcls;

    exedirc=argc[1];
    dirc=argc[2];
    subdirc=argc[3];
    lat_top=argc[4];
    lat_bottom=argc[5];
    lon_left=argc[6];
    lon_right=argc[7];
    beg_year=argc[8];
    end_year=argc[9];
    numcls=atoi(argc[10]);


    tgtdirc=dirc+"/"+subdirc;

    command="mkdir "+tgtdirc;
    system(command.c_str());


    ofname=tgtdirc+"/load_landsat_data_"+subdirc+".sh";
    writescript_urban(exedirc, ofname, tgtdirc,lat_top, lat_bottom, lon_left, lon_right, beg_year, end_year);

    ofname=tgtdirc+"/create_tsmask_"+subdirc+".sh";
    writescript_tsmask(exedirc, ofname, tgtdirc, beg_year, end_year);

    ofname=tgtdirc+"/create_indices_"+subdirc+".sh";
    writescript_indices(exedirc, ofname, tgtdirc, beg_year, end_year);

    ofname=tgtdirc+"/create_clusters_"+subdirc+".sh";
    writescript_clusters(exedirc, ofname, tgtdirc, beg_year, end_year, numcls);

    ofname=tgtdirc+"/remove_tsdata_"+subdirc+".sh";
    writescript_cleanups(ofname, tgtdirc, beg_year, end_year);

    ofname=tgtdirc+"/map_raw_class_"+subdirc+".sh";
    writescript_maprawclass(exedirc, ofname, dirc, subdirc, beg_year, end_year, numcls);


    ofname=tgtdirc+"/urban_change_"+subdirc+".sh";
    writescript_detection(exedirc, ofname, dirc, subdirc, beg_year, end_year);
    
    
    
    ofname=tgtdirc+"/urban_detection_run_all_"+subdirc+".sh";
    writescript_run_all(ofname, dirc, subdirc);





    
    command="chmod +x "+tgtdirc+"/*.sh";
    system(command.c_str());


    return 0;
}
