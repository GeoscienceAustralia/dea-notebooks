#
#	Makefile for M1
#

#CFLAGS = -Wall -O2 -g2 -lgsl -lgslcblas 
#CFLAGS = -Wall -O2 -fpermissive -qopenmp -march=corei7-avx -lgsl -lgslcblas -lm -lpthread 
#CFLAGS = -Wall -O2 -fpermissive -fopenmp -march=corei7-avx -lgsl -lm -lpthread 
CFLAGS = -Wall -O2 -fpermissive -fopenmp -lgsl -lgslcblas -lm -lpthread 
#CFLAGS = -Wall -O2 -ftree-vectorize -fopenmp -mtune=core2 -lgsl -lgslcblas -lm
#CFLAGS = -Wall -O2  -lgsl -lcblas -lm
#CFLAGS = -Wall -O2 -g2 -march=i686 -static -static-libgcc -lgsl -lgslcblas -lm
#CFLAGS = -O2 -g2 -march=athlon-xp -static -static-libgcc -lgsl -lgslcblas -lm
#CFLAGS = -Wall  -march=athlon-xp -lgsl -lgslcblas -lm
#CFLAGS = -Wall -O2 -g2 

URBOBJS= urban.o comm.o statsml.o 
TMMOBJS= tsmask_multiyears.o comm.o statsml.o 
SBCOBJS= suburbchange.o comm.o statsml.o 
VDIOBJS= vdi_urban_scripts.o comm.o statsml.o 
MAPOBJS= maprawclass.o comm.o  
TMPOBJS= temporal_filter.o comm.o statsml.o 



%.o : %.cpp 
#	icpc -openmp -march=core2 -fast -c $*.cpp 
#	icpc -openmp -march=corei7-avx -fast -c $*.cpp 
	g++ -fopenmp -fpermissive -march=core2 -O2 -c $*.cpp 

all : urb tmm sbc vdi map   


urb: $(URBOBJS)
	g++ -o urban $(URBOBJS) $(CFLAGS)

tmm: $(TMMOBJS)
	g++ -o tsmask_multiyears $(TMMOBJS) $(CFLAGS)

sbc: $(SBCOBJS)
	g++ -o suburbchange $(SBCOBJS) $(CFLAGS)

vdi: $(VDIOBJS)
	g++ -o vdi_urban_scripts $(VDIOBJS) $(CFLAGS)

map: $(MAPOBJS)
	g++ -o maprawclass $(MAPOBJS) $(CFLAGS)

tmp: $(TMPOBJS)
	g++ -o temporal_filter $(TMPOBJS) $(CFLAGS)


clean:
	rm -f *.o test 

new: clean all

