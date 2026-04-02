#include <bits/stdc++.h>
#include <ext/pb_ds/assoc_container.hpp>
#include <ext/pb_ds/tree_policy.hpp>
using namespace std;
using namespace __gnu_pbds;
#define int long long
#define ld long double
#define pii pair<int, int>
#define i128 __int128_t
#define ar array
#define pb emplace_back
#define all(x) (x).begin(), (x).end()
#define lb(v, x) (int)(lower_bound(all(v), x)-(v).begin())
#define up(v, x) (int)(upper_bound(all(v), x)-(v).begin())
#define fi first
#define se second
#define sz(x) (int)(x.size())
#define yes "Yes"
#define no "No"
#define endl '\n'

template <typename T>
using ordered_set = tree<T, null_type, less<T>, rb_tree_tag, tree_order_statistics_node_update>;

template<class T>
istream &operator>>(istream &is, const vector<T> &v) {
    for (auto &x:v) is >> x;
    return is;
}

template<class T>
ostream &operator<<(ostream &os, const vector<T> &v) {
    for (const auto &x:v) os << x << " ";
    return os;
}

template<class T>
void chmin(T &a, T b) { a=min(a, b); }
template<class T>
void chmax(T &a, T b) { a=max(a, b); }

void reset() { 
    
}

void solve() {

}

signed main() {
    cin.tie(0)->sync_with_stdio(0);
    int t=1;
    cin >> t;
    while (t--) 
        solve();
    return 0;
}
