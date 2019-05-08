
//#include "dtree.h"

#include "comm.h"

struct Node
{
    Node** sons;
    short* cutpoints;
    size_t* hisg;
    size_t binnum;
    int ncp;
    int level;
    int tgd;
} ;




// Calculate the covariance matrix of  a set of data, the data is specified by matrix X, 
// the data vectors are placed as row vectors in X so
// if each data has m features and there are total n data in the set, then
// X is an  n x m matrix, output matrix will be an m x m symmetric matrix

int covmatrix(gsl_matrix* blk, gsl_matrix*& cvm);


// Calculate the Mahalanobis distance between vector v1 and v2, icvm store the INVERT of the covariance matrix 
double mahdistance(gsl_vector* v1, gsl_vector* v2, gsl_matrix* icvm);

 
int calcores(gsl_matrix* cores, int* acls, gsl_matrix* ma, int nc);

//Calculate the score for a cluster solution, which is the sum of Mahalanobis distance between vectors from different cluster minus  the sum of Mahalanobis distance vectors from the same cluster
double clusterscores(gsl_matrix* data, gsl_matrix* icvm, int** signtab);

double tryoneprojection(gsl_matrix* ma, int** signtab,  gsl_matrix* mp);

// vary the (x, y) coefficient of the projection matrix N times to find the optimal projection matrix mp which maximise the merit
double trymultiprojection(gsl_matrix* ma, int** signtab,  gsl_matrix* mp, int N, int x, int y, double& ut, double& sigma, double tail);

// Project a set of vector (in data) by matrix mp, return
float** dataproj(float** data, gsl_matrix* mp, int irow);


int KNNclassifyraw(float* data, gsl_matrix* mp, gsl_matrix* tpoints, int* acls,  gsl_matrix* icvm, int M, int K, double*&);

// K Nearest Neighbour classifier
int KNNclassify(gsl_vector* v1, gsl_matrix* tpoints, int* acls,  gsl_matrix* icvm, int M, int K, double*&);

// Find the optimal K for KNN classifier for the training set tpoints
int findK(gsl_matrix* tpoints, int* acls,  gsl_matrix* icvm, int M, int maxK);

// Return the inverse of a matrix
gsl_matrix* invmatrix(gsl_matrix* cvm);

int findicvm(gsl_matrix* ma, gsl_matrix* icvm);


// x -- row index of the top left conner
// y -- column index of the top left conner
// irow -- # of row in the block
// icol -- # of columns in the block
// *ida -- array storing the order of pixel index
// rs --- # of pixels in one row of the original file
// bsthod -- maximum size of a block that can be unmix in one round
int genorders(int x, int y, int irow, int icol, int* ida, int& pc, int rs, int bsthod);


// Calculate a set of generic statistics of a time series
double* tscoeffs(double* ts, int bidx, int eidx, int nts);

// Calculate the covariance matrix of  a set of data, the data is specified by matrix X, 
// the data vectors are placed as column vectors in X so
// if each data has m features and there are total n data in the set, then
// X is an m x n matrix, output matrix will be an m x m symmetric matrix

gsl_matrix* covmatrix_col(gsl_matrix* X);


// Calculate the covariance matrix of  a set of data, the data is specified by matrix X, 
// the data vectors are placed as row vectors in X so
// if each data has m features and there are total n data in the set, then
// X is an  n x m matrix, output matrix will be an m x m symmetric matrix

gsl_matrix* covmatrix_row(gsl_matrix* X);

// Principal component analysis on a set of data specified in X, 
// the data vectors are placed as column vectors in X so
// if each data has m features and there are total n data in the set, then
// X will be an m x n matrix, out put the ordered m components as column vectors of the output matrix
// which will be and m x n matrix

gsl_matrix* pca(gsl_matrix* X);

//MML message length of an Gaussian distribution
double guasmml(double* x, int N, double dta);

// Remove noisy data from time series, using rate of rise and rate of drop 
bool remoutliners(double** data, int ss, int ind, double dta);
bool remoutliners_gs(double** data, int ss, int ind, double dta, double ivd, double ivd2);


int spatialfilter(double** data, double* lme,  int band, int icol, int rowmin, int rowmax, int colmin, int colmax,
	int x, int y, int width, double thod);


int findtails(double ** data, int ind, int bands, double ivd, int*& tails, int& nt, double rt, int dr);



double findbaseline(double* ts, int bands, double ivd, double dta);

double* advtscoeffs(double* ts, int bands, int bidx, int eidx, int minp, int maxp, int ans, int);

// Centre data on each dimension (row) of set X
int centre(gsl_matrix* X);

int standardarray(double* data, int pnum, double ivd);

int standardarray_f(float* data, int pnum, float ivd);

// standarise data on each dimension (row) of set X
int standarise(gsl_matrix* X);

// Generate a kernel matrix from data matrix X
// X -- the set of input data, where each column of X represents an instance of the data
// centred -- if it is true, calculated the centred version of the kernel, otherwise just calculate using original data
// kt -- the type of kernel function
// np -- the number of parameters of the kernel function
// pa -- the list of the parameters

gsl_matrix* findakernel(gsl_matrix* X, bool centred, int kt, double* pa, double& sum, double*& colsum);

// calculate the value of kernel function specified by kt and pa of input vector v1 and v2
double calkernel(gsl_vector* v1, gsl_vector* v2, int kt, double* pa);


//  Return normalized eigenvalues and eigenvector of real symmetric matrix X
//  eigenvalues are sorted in descendent order and stored in vector eval
//  while the corresponding eigenvector are stored in the columns of the matrix evec
int basicpca(gsl_matrix* X, gsl_vector*& eval, gsl_matrix*& evec);

int kernelpca(gsl_matrix* X, int kt, double* pa, gsl_vector*& eval, gsl_matrix*& evec, int& p, double& sum, double*& colsum);

int fspacenormalised( gsl_vector* eval, gsl_matrix* evec);

// Return the first p kernel PC of vector x given 
double* kpcacoeffs(gsl_matrix* X, int kt, double* pa, gsl_vector* x, gsl_matrix* evec, double sum, double* colsum, int p);


// Support vector clustering
int SVclustering(gsl_matrix* X,  double v,  int kt, double* pa, int& nc, int* cls, svminfo*);

int SVclustering_wf(gsl_matrix* XX,  double v,  int kt, double* pa, int& nc, int*& xcls, double ivd);
// Trend analysis
double* trendcoeffs(double* ts, int bands, int bx1,  int years, int sam, int ans, int tpres);

// find a pair of coefficients to be updated 
int scan_kkt(gsl_rng*, int ty, int m, double* fw, double* a, double ph, double rvm, int& i, int& j);

// find a pair of coefficients to be updated 
int scan_kkt_v2(gsl_rng* rng, int ty, int m, double* fw, double* a, double ph, double rvm, int& i, int& j);

double	hyperdistance(gsl_matrix* K, gsl_vector* a, int ind);

// Generate an array of random number in a which are sum to 1
int randomsimplex(gsl_rng*, double* a, int m);


// Generate a random permutation of m
size_t* randomperm(gsl_rng*, int m);

// Generate a random permutation of n out of m instances
size_t* randomperm(gsl_rng* rng, int m, int n);

// Generate a random permutation of n out of m instances, excluding invalid data
size_t* randomperm(gsl_rng* rng, int m, double ssr, int& n, float* data, double ivd);

// update a pair of coefficients
int updatecoeffs(gsl_matrix* K, double* a, double* fw, int i, int j, double rvm, double&);



// Check weather vector pi and pj belong to the same cluster by sampling ss points between pi and pj
bool adjcheck(gsl_matrix* X, int i, int j, int ss, double* a, int kt, double* pa, double rsq, double sum);

bool adjcheck2v(gsl_vector* pi, gsl_vector* pj, double* a, int kt, double* pa, double sum, double rsq, int ss, gsl_matrix* X);
double calrsq(gsl_vector* px, double* a, gsl_matrix* X, int kt, double* pa, double sum);

// Label the data according to the adjacency matrix adj
//
int inducecluster(bool** adj, double* a, int m, int& nc, int* cls, double rvm);


int inducecluster_oned(bool* adj, bool* chk, int i, double* a, int m, int& nc, int* cls, double rvm);


int inducecluster_sv(int svcc, int* svind, int m, gsl_matrix* K, int* svcls, int* cls);


int inducecluster_sv2(int svcc, int* svind, bool** adj, gsl_matrix* X, int sam, double* a, int kt, double* pa, double rsq,  double sum,  int& nc, int* cls);

int inducecluster_sv3(int svcc, int* svind, bool** adj, gsl_matrix* X, int sam,  int kt, double* pa,  int& nc, int* cls, svminfo* svf);

// Create clusters according to coefficients array a
int createcluster_v1(gsl_matrix* X, double* a, gsl_rng* rng, int sam, int kt, double* pa, double rsq, double sum, double rvm, int& nc, int* cls);


// Create clusters according to coefficients array a
int createcluster_v2(gsl_matrix* X, gsl_matrix* K, double* a, int sam, int kt, double* pa, double rsq, double sum, double rvm, int& nc, int* cls);


// Create clusters according to coefficients array a
int createcluster_v3(gsl_matrix* X, gsl_matrix* K,  int sam, int kt, double* pa, double rvm, int& nc, int* cls, svminfo* svf);

int relables(int* cls, int m, double v, int& nc);

// See if there clusters can be merged
int mergeclusters(gsl_rng* rng, int* cls, int ps, int sam, double* a, gsl_matrix* X, int kt, double* pa, double rsq, double sum, int& nc);

int addsamples(gsl_rng* rng, int* list, int cur, int ps, int clabel, int* pnd, size_t* sts);

int adjustcluster(int* cls, int nc, gsl_matrix* K);

double diskcore(gsl_matrix* K, int i, int *cdexj, int ss, double ksumj);


// find all the point connect to point h directly or indirectly
int findgroup(int h, int m, bool** adj, int& pp, int* cdex, bool* chk);

// Find the data point which maximises the gain for SMO algorithm
int findsmoj(int i, int m, double* a, double* fw, double rvm, double esma);

// Generate clusters from adjacency matrix adj
int clusterfromgraph(bool** adj, int m, int& nc, int*& cls);


// Using SVC algorithm to cluster a rectangle subset of an image, the rectangle is specified by the 
// coordinate of the top left corner (x, y) and the number of row and the number of the column of the
// subset row, and col
//


int clusterablock(double** data, int irow, int icol, int bands,  int x, int y, int row, int col,
	double v,  int kt, double* pa, int& nc, int*& cls, double);


int clusteroneimage(double** data, int natb, int icol, int irow, int bs, double v, int kt, double* pa, int& nc, int*& cls, double ivd, string fimgout);


int samplingaset(gsl_rng* rng, int* cls, int pnum, int* idx, int bs);

int samplingexset(gsl_rng* rng, int* cls, int pnum, int* idx, int bs, short* rsflags);

// Find k nearest neighbours of the pixel with index# ind 
int* knnindex(double** data, int icol, int irow, int natb, int ind,  int width, int k, int* cls, int sam, int kt, double* pa, svminfo* svf, gsl_matrix* X, short*);

// House keeping, eliminate (assign class label 0) to the clusters whose size are less than thd
int consolidate(int* cls, int m, int thd, int& nc);

int getsvfsvind(int* cls, int* svind, int svcc, int nc, svminfo* svf);

int calrsflags(double** data, int i, int kt, double* pa, double *a, double rsq, double sum, gsl_matrix* X);

int checkcls(double** data, int ind, int sam, int kt, double* pa, gsl_matrix* X, svminfo* svf);


int connclusters_v2(int cp,  int** olidx, int* olcdx, int* snc, int** scls, int** ridx, int* ccdx,  int* cls, int& nc);
int connclusters(int cp, int** olidx, int* olcdx, int* snc, int** scls, int** cidx, int* ccdx, int* cls, int& nc);

int cluster_oneset(double** data, int natb, int pnum, int cr, int* scheme, double v,double tao, double olv, int* idx, int& nc, int*& cls);	
int cluster_atomset(double** data, int natb, int pnum, double v, double tao, int* idx, int& nc, int*& cls);

int clusteroneimage_v2(double** data, int natb, int pnum, int* scheme, double v, double tao, double olv, int& nc, int*& cls, double ivd);

int divideoneset(double** data, int pnum, int cr, int bs, double v, int* idx, int**& cidx, int**& olidx, int*& ccdx,
	int*& olcdx, int**& ridx);

double* classcount(float* cls, int nc, int pnum);

int sortclusters(int* cls, int nc, int pnum);
int sortclusters(float* cls, int nc, int pnum);
int sortclusters(float* cls, float* vals, int nc, unsigned long pnum, bool des);

int findnc(float* cls, int pnum);

int findclusterNN(float** data, int natb, float* wcls, int nc, int ind, int irow, int icol, int width, int cth);

int assignotlabels(float** data, int natb, float* wcls, int nc, double* cnm, double thd, int irow, int icol, int width, int cth);

int findcth(double* cnm, int nc);

Rblock** createRBlist(float** data, int irow, int icol, int natb, int bs, float* wcls, int cth, int& nb, int& nrow, int& ncol);

Rblock* createRblock(int px, int py, int rs, int cs, int icol, int natb, float** data, float* wcls, int cth);

int assignotlabels_v2(float** data, int irow, int icol, int nia, int bs, int cth, float* wcls);

size_t* findNNblocks(int x, int y, int nrow, int ncol, int n, gsl_rng* rng);

int clsRblock(Rblock** rblist, int bid,  int nrow, int ncol, int icol, int natb, float** data, float* wcls, float* cls, int cth, int k);

int delRBlist(Rblock** rblist, int nb);

int delRblock(Rblock* rb);

float clsNNpix(int ind, float** data, int natb, int sds, gsl_matrix* Y, gsl_vector* ny, Rblock* rb, float* wcls, int cth, int k);

int findYmatrix(Rblock** rblist, int bid, int natb, float** data, int nrow, int ncol, int thd, float* wcls, gsl_matrix*& Y, 
	gsl_vector*& ny, float*& ycls);

int countneigbours(int pnum, int irow, int icol, float* wcls, int nc, int**& nbs);

int countonetype(int ty, int pnum, int irow, int icol, float* wcls, int nc, int** nbs);

int setoneband(int vpn, int* idx, float* dst, float* src);

int readvalidpixels(string imgfname, int pnum, int bands, float**& data, int*& idx, float ivd);

int findmatch(double* sums, float** data, int* idx, int vpn, int bands, float** sdata, int dj);


// to determine if a point (x,y) is inside a  convex polygon whose vertex are specified the array vx and vy, 
// nc is the number of the vertex, return -1 if the point is outside the polygon, 
// 0 if it is on one of the edge of the polygon, 1 if it is inside the polygon

int insidepolygon(double* vx, double* vy, int nc, double x, double y);

size_t readmaskfile(string fname, size_t pnum, char target, size_t*& idxlist);

int checksubts(double* ts, size_t bands, double* x, double* y, size_t stp, size_t slen, size_t mlen, size_t sendp, double ivd, double* sps);

int segmentts(short* raw, size_t idx, size_t bands, size_t pnum, size_t minlen, size_t minla, size_t endp, double ivd, double*& states);

int assigndna(double* seginfo, size_t ss, size_t dnapt, double* ths, int* dims, char* dna);


size_t readtsmeta(string metafname, size_t* mhead, size_t*& idxlist);


int readsegmeta(string segmetafname, size_t vpnum, short*& segnum);
int findcutpoints(size_t* hisg, size_t binnum, size_t ncp, size_t*& cpts);

// Find the corresponding sub-sequence given the start value and the length
int findsubseg(size_t st, size_t slen, size_t bands, size_t didx, size_t seglen, short* dnalen, size_t& dst, size_t& dlen);


int readseglen(string segdatafname, size_t segtotal, short*& dnalen);
int readseglen_static(string segdatafname, size_t segtotal, short* dnalen);

Node* createnode(int level, int ncp, size_t binnum, int tgd);

int deletetree(struct Node* nd);

int createsonnodes(Node* nd, int level, int ncp, int binnum, int tgd);

short assignlabel(Node* nd, size_t idx, int nc,  short* bindata, short& label, int* digit);


int write_anode(ofstream& fout, Node* nd);


int write_subtree(ofstream& fout, Node* nd, int nc);

int output_tree(string cutpoints_fname, Node* root, int nc);

int create_subtree(ifstream& fin, Node*& nd, int nc);



int input_tree(string cutpoints_fname, Node*& root, int nc);


// Generate DNA for one class 

short* gendna(string binfname, size_t blocksize, size_t sgn, int nc, int* digit, Node* root);


int getbandtimes(string bandnames, int bands, double* bandtimes);


int gettoffs(double* alltoffs, long tosnum, long tcol, double* bandtimes, int bands, int lat, int lon, double*& toffs);

int readtidaloffsets(string fname, long& tosnum, long& tcol, double*& toffs);

int getatom(string st, int pos, int len);

int findneighbours(double* toffs, long N, double ivd, long*& ngb); 
    


