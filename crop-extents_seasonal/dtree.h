#include "statsml.h"

struct TNode
{
    int _arc;
    int _vid;     // index number of the variable for the cut point(s)
    double* _paras; // parameters for the node
    TNode** _children;
};


TNode* createnode(int arc);

int deletetree(TNode* nd);

double mum_msglen(size_t* counts, int arc);


double cut_msglen(size_t* lf_labc, size_t* rt_labc, int arc);


int est_multinomial(int* glabs, size_t* idxlist, long bidx, long eidx, int arc, double*& paras);

// Find single cut point for the array data
// cudcuts  -- number of candidate cut points to search
// rndrng -- randomness, 0 means return the best cut, 1 means totally random selection of the cut point
// num -- number of data point in array data

long findunisplit(double* data, int* labs, long num, int arc, long cndcuts, double rndrng, double& cutval, size_t* sts);
TNode* buildtree(double* raw, int nd,  int* glabs, long num, size_t* idxlist, int arc, long cndcuts, double rndrng, int cur_depth, int maxdepth);

TNode* findleaf(TNode* root, double* data, int nd, long idx);
int dtclassifier(TNode* root, double* data, int nd, long idx, double*& cdis);

TNode* buildtree(double* raw, int nd,  int* glabs, long num, size_t* idxlist, int arc, long cndcuts, double rndrng, int cur_depth, int maxdepth);


TNode* readanode(double* data, size_t& pos);

int readatree(string ifname, TNode*& root);

int writeatree(ofstream& fout, TNode* root);

int readaforest(string ifname, vector<TNode*>& dforest);
int writeaforest(string ofname, vector<TNode*>& dforest);
int writeaforest(string ofname, TNode** dforest, size_t ss);
int deleteforest(vector<TNode*>& forest);
int deleteforest(TNode** forest, int fstsize);
int forestclassifier(vector<TNode*>& dforest, double* data, int nd, long idx, double*& clsd);
int forestclassifier(TNode** dforest, int fstsize, double* data, int nd, long idx, double*& clsd);
int classifyaset(vector<TNode*>& dforest, double* data, int nd, long pnum, float*& pr);
int classifyaset(TNode** dforest, size_t fstsize, double* data, int nd, long pnum, float*& pr);
int varmapping(TNode* nd, size_t* sels);
int dfvarmapping(TNode** dforest, int fstsize, size_t* sels);
/*
int reconstructatree(ifstream& fin, int len, Node* nd);

int writeatree(ofstream& fout, Node* nd);
    
int deleteatree(Node* nd);
    
int displayatree(Node* nd, string* atb_names, int depth);

//Node* classifybyatree(Node* nd, float* data, int& cls, float* est, int nc);
Node* classifybyatree(Node* nd, float* data, int& cls, double* est, int nc);

string ftostr( float value );

string itostr( int value );
    
int get_arclabels(float* paras, string* atb_names, string* arclabels, int nc);


// Search the best hyperplane, two classes only version
double findbesthp(float** data,  int* acls,  int* dsub, int dn, int* asub, int an, float* paras);


// Assign the instances in uncertainty region into the high confidence region using priors inferred from the instances in uncertainty region
//
int disunreg(double** ccs, double lpc, double&, double&);

double trmmsg(double** ccs, double lpc, double&, double&); // For two classes only

int splitanode(Node* nd, int arity, int len, float* paras);

Node* fillatree(Node* nd, float** data, int* acls, int irow, int nc, double lpc);

int inferatree(Node* nd, float** data, int* acls, int* dsub, int dn, int an, int natb, gsl_rng* rng, size_t* sts, float** paras);

int splitdata(Node* nd, float** data, int* dsub, int dn, int** subinds, int* subdns, int ns, int nc);

int writeaforest(Node** treelist, string ofname, int ntrees);

int reconstructaforest(Node**& treelist, string ifname, int ntrees);

//int classifybyaforest(Node** treelist, int ntrees, float* data, int& cls, float* est, int nc);
int classifybyaforest(Node** treelist, int ntrees, float* data, int& cls, double* est, int nc);
int classifybyaforestv1(Node** treelist, int ntrees, float* data, int& cls, double* est, int nc);

//int classifyby3forests(vector<Node**>& threetreelists, int ntrees, float* data, int& cls, float* est, int nc);
int classifyby3forests(vector<Node**>& threetreelists, int ntrees, float* data, int& cls, double* est, int nc);
int classifyby3forestsv1(vector<Node**>& threetreelists, int ntrees, float* data, int& cls, double* est, int nc);

int readnamefile(string ifname, string*& classlabels, int& nc, string*& atbnames, int& ntab);


int treetravers(vector<Node*>& nodelist, Node* nd);

*/
