#include <bits/stdc++.h>
// #include <bits/extc++.h>
#include <ext/pb_ds/assoc_container.hpp>
#include <ext/pb_ds/tree_policy.hpp>
using namespace std;
using namespace __gnu_pbds;
#define int long long
#define pii pair<int, int>
#define i128 __int128_t

template <typename T>
using ordered_set = tree<T, null_type, less<T>, rb_tree_tag, tree_order_statistics_node_update>;

template<class T>
istream &operator>>(istream &is, vector<T> &v) {
    for (auto &x : v) is >> x;
    return is;
}

template<class T>
ostream &operator<<(ostream &os, const vector<T> &v) {
    for (const auto &x : v) os << x << " ";
    return os;
}


// mod
template<int P>
struct MInt {
    int x;
    constexpr MInt() : x(0) {}
    template<class T>
    constexpr MInt(T x) : x(norm(x% P)) {}
    constexpr static int norm(int x) {
        return x < 0 ? x + P : x >= P ? x - P : x;
    }
    constexpr MInt inv() const {
        int a = x, b = P, u = 1, v = 0;
        while(b) {
            int t = a / b;
            swap((a -= t * b), b);
            swap((u -= t * v), v);
        }
        return u;
    }
    constexpr MInt operator-() const {
        return MInt() - *this;
    }
    constexpr MInt& operator+=(const MInt& a) {
        x = norm(x + a.x);
        return *this;
    }
    constexpr MInt& operator-=(const MInt& a) {
        x = norm(x - a.x);
        return *this;
    }
    constexpr MInt& operator*=(const MInt& a) {
        x = 1ll * x * a.x % P;
        return *this;
    }
    constexpr MInt& operator/=(const MInt& a) {
        assert(a);
        return *this *= a.inv();
    }
    constexpr friend MInt operator+(MInt l, const MInt& r) {
        return l += r;
    }
    constexpr friend MInt operator-(MInt l, const MInt& r) {
        return l -= r;
    }
    constexpr friend MInt operator*(MInt l, const MInt& r) {
        return l *= r;
    }
    constexpr friend MInt operator/(MInt l, const MInt& r) {
        return l /= r;
    }
    constexpr explicit operator bool()const {
        return x != 0;
    }
    constexpr bool operator!()const {
        return x == 0;
    }
    friend ostream& operator<<(ostream& os, const MInt& a) {
        return os << a.x;
    }
    string find_Fraction()const {
        for(int i = 1; i <= 1000000; ++i)
            if((*this * i).x <= 100)
                return to_string((*this * i).x) + "/" + to_string(i);
        return "not find.";
    }
};
constexpr int P = 1e9 + 7;
using Z = MInt<P>;
constexpr Z power(Z a, int b) {
    assert(b >= 0);
    Z ans(1);
    for(; b; b >>= 1, a *= a)
        if(b & 1) ans *= a;
    return ans;
}
template<int V>// invV<2> * 2 ==1 mod P
constexpr Z invV = power(V, P - 2);

// dsu
constexpr int mxN=2e5+5, inf=1e18;
int rep[mxN], R[mxN];
int find(int u){
    return (rep[u]==u?u:(rep[u]=find(rep[u])));
}

bool unite(int i, int j){
    int ri=find(i);
    int rj=find(j);
    if (ri==rj) return false;
    if (R[ri]<R[rj])
        rep[ri]=rj;
    else if (R[ri]>R[rj])
        rep[rj]=ri;
    else
        rep[rj]=ri, ++R[ri];
    return true;
}


// Fenwick Tree
int F[mxN];
void update(int i, int v) {
    for (++i;i<mxN;i+=i&(-i))
        F[i]+=v;
}

int query(int i) {
    int ret=0;
    for (++i;i>0;i-=i&(-i))
        ret+=F[i];
    return ret;
}
// T[l]=sum[0, l];

// dijkstras
vector<pii>adj[mxN];
int dist[mxN];
void dijkstras(){
    priority_queue<pii, vector<pii>, greater<pii>>pq;
    while (pq.size()){
        auto [d, u]=pq.top();
        pq.pop();
        if (d!=dist[u]) continue;
        for (auto &[v, w]:adj[u]) {
            if (dist[v]>dist[u]+w){
                pq.push({dist[v]=dist[u]+w, v});
            }
        }
    }
}

// bitmask dp
int dp[1<<20];

void bitmaskdp(){
    // job assignment problem
    int n=20;
    fill(dp, dp+(1<<20), 1e9);
    vector<vector<int>>cost(n, vector<int>(n)); //cost[i][j]=ith person on jth job
    // dp[mask]=min cost assigning first pop_count(mask) workers to subset mask jobs
    // dp[0]=0;
    for (int i=1;i<1<<n;++i) {
        int k=__builtin_popcount(i);
        for (int j=0;j<n;++j) {
            if ((1<<j)&i){
                dp[i]=min(dp[i], dp[i^(1<<j)]+cost[k-1][j]);
            }
        }
    }
}

void bitmaskdpsubset(){
    int n=20;
    for (int mask=0;mask<1<<n;++mask) {
        for (int submask=mask;submask!=0;submask=(submask-1)&mask){
            int subset=mask^submask;
            // do whatever
        }
    }
}

// SegTree
struct SegTree {
    int n;
    vector<int>tree;
   
    SegTree(int n):n(n) {
        tree.resize(4*n);
    }
   
    void build(vector<int>&A, int node, int l, int r) {
        if (l==r) {
            tree[node]=A[l];
            return;
        }
        int mid=l+(r-l)/2;
        build(A, node*2, l, mid);
        build(A, node*2+1, mid+1, r);
        tree[node]=min(tree[node*2], tree[node*2+1]);
    }
   
    void update(int node, int l, int r, int idx, int val) {
        if (l==r) {
            tree[node]=val;
            return;
        }
        int mid=l+(r-l)/2;
       
        if (idx<=mid)
            update(node*2, l, mid, idx, val);
        else
            update(node*2+1, mid+1, r, idx, val);
           
        tree[node]=min(tree[node*2], tree[node*2+1]);
    }
   
    int query(int node, int l, int r, int ql, int qr) {
        if (ql>r || qr<l) return inf;
        int mid=l+(r-l)/2;
        if (ql<=l && r<=qr) return tree[node];
        return min(query(node*2, l, mid, ql, qr), query(node*2+1, mid+1, r, ql, qr));
    }
};
// ql qr inclusive 0 indexed

void solve() {
    i128 x=0;
}

signed main() {
    // file input
    // ifstream cin("input.txt");
    cin.tie(0)->sync_with_stdio(0);
    int t=1;
    cin >> t;
    while (t--) 
        solve();
    return 0;
}
