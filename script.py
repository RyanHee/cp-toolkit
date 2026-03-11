import os
import subprocess
import string
import sys
import json
from pathlib import Path
import glob
import shutil  # NEW: for javac/java detection
import difflib

# ---- Toolchain & flags (edit if needed) ----
GPP = r"C:/msys64/mingw64/bin/g++.exe"  # your g++
STD = "-std=gnu++17"                    # C++17 with g++
EXTRA_WARN = ["-Wall", "-Wextra", "-Wpedantic"]

CPP_TEMPLATE = """#include <bits/stdc++.h>
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

template<class T>
void chmin(T &a, T b) { a=min(a, b); }
template<class T>
void chmax(T &a, T b) { a=max(a, b); }

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
"""

# NEW: Java 模板（类名会与文件名一致：A.java -> public class A）
JAVA_TEMPLATE = """import java.io.*;
import java.util.*;

public class %CLASS% {

    static void solve(BufferedReader br, PrintWriter out) throws IOException {
        
    }
    
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        PrintWriter out = new PrintWriter(new BufferedOutputStream(System.out));

        int t;
        t = Integer.parseInt(br.readLine().trim());

        while (t-- > 0)
            solve(br, out);

        out.flush();
    }
}
"""

OUTPUT_EXTS = {'.out', '.ans', '.expected'}  # 单目录保底识别输出用；双目录则不限制扩展名

def _canon_text(s: str) -> str:
    # Remove UTF-8 BOM (if present), normalize newlines, and strip trailing spaces ONLY.
    s = s.lstrip("\ufeff")
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    lines = s.split('\n')
    lines = [ln.rstrip() for ln in lines]  # ONLY trailing spaces ignored
    return "\n".join(lines)

def _show_invisibles(s: str) -> str:
    # Visualize spaces and control chars: space→·, tab→⇥, show line ends
    s = s.replace('\r', '␍').replace('\t', '⇥')
    return "\n".join(ln.replace(" ", "·") + "⏎" for ln in s.split("\n"))

def _compare_and_report(src_filename: str, in_path: str, output: str, expected_output: str) -> None:
    canon_out = _canon_text(output)
    canon_exp = _canon_text(expected_output)
    tag = os.path.basename(in_path)

    if canon_out == canon_exp:
        print(f"✅ {src_filename} passed on {tag}")
        return

    print(f"❌ {src_filename} failed on {tag}")
    print("---- Expected (visible) ----")
    print(_show_invisibles(canon_exp))
    print("----   Got (visible)   ----")
    print(_show_invisibles(canon_out))
    print("---- Unified Diff ----")
    diff = difflib.unified_diff(
        canon_exp.splitlines(), canon_out.splitlines(),
        fromfile='expected', tofile='output', lineterm=''
    )
    print("\n".join(diff))


def _alpha_index_from_filename(src_path: str) -> int:
    base = os.path.basename(src_path)
    letter = base.split('.')[0][:1].upper()
    if not ('A' <= letter <= 'Z'):
        raise ValueError(f"Cannot derive alphabetical index from {base}")
    return ord(letter) - ord('A')

def _sorted_files(dir_path: str):
    """列出目录下所有普通文件（不含子目录与隐藏文件），按文件名排序。"""
    if not os.path.isdir(dir_path):
        return []
    all_paths = [os.path.join(dir_path, name) for name in os.listdir(dir_path)]
    files = [p for p in all_paths if os.path.isfile(p) and not os.path.basename(p).startswith('.')]
    return sorted(files, key=lambda p: os.path.basename(p).lower())

# ---------------- C++ build ----------------
def compile_cpp(file_path: str):
    exe_path = file_path.replace(".cpp", ".exe")
    directory = os.path.dirname(file_path)
    include_dir = os.path.join(directory, "include")
    include_flag = [f"-I{include_dir}"] if os.path.exists(include_dir) else []
    compile_cmd = [GPP, STD, *EXTRA_WARN, *include_flag, file_path, "-o", exe_path]
    result = subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        print(f"Compiled (C++): {file_path}")
        return exe_path
    else:
        print(f"Compilation failed for {file_path}:\n{result.stderr.decode()}")
        return None

# ---------------- Java build/run helpers (NEW) ----------------
def compile_java(file_path: str):
    """
    编译单个 .java 文件。要求：public class 与文件名同名。
    返回 (run_cmd_list, display_name)
    """
    if shutil.which("javac") is None or shutil.which("java") is None:
        print("javac/java 未在 PATH 中，无法编译/运行 Java。请先安装 JDK 并将其加入 PATH。")
        return None, None

    src_dir = os.path.dirname(file_path) or "."
    base = os.path.basename(file_path)
    class_name = os.path.splitext(base)[0]  # 假设 public class 与文件名一致

    result = subprocess.run(["javac", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"Compilation failed for {file_path}:\n{result.stderr.decode()}")
        return None, None

    run_cmd = ["java", "-cp", src_dir, class_name]
    return run_cmd, f"{class_name}.class"

def build_and_get_runner(file_path: str):
    """
    统一入口：根据扩展名选择 C++ 或 Java 的编译与运行方式。
    返回 (run_cmd_list, display_name)
      - C++：run_cmd_list = [<exe_path>]
      - Java：run_cmd_list = ["java", "-cp", <dir>, <MainClass>]
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".cpp":
        exe = compile_cpp(file_path)
        if exe:
            return [exe], os.path.basename(exe)
        return None, None
    elif ext == ".java":
        return compile_java(file_path)
    else:
        print(f"不支持的文件类型：{file_path}（仅支持 .cpp 与 .java）")
        return None, None

# ---------------- run single test (cpp or java) ----------------
def run_single_test(problem_folder: str, src_filename: str):
    """
    编译并运行 <src_filename>（.cpp 或 .java）：
      - 优先从 <problem_folder>/tests/in 与 tests/out 读取用例（扩展名不限）
      - 若无 in/out 子目录：从 <problem_folder>/tests 混放目录里按扩展推断输入/输出
      - A=第1个，B=第2个…… 取第 N 个输入与第 N 个输出进行对拍。
    """
    src_path = os.path.join(problem_folder, src_filename)
    if not os.path.exists(src_path):
        print(f"File not found: {src_path}")
        return

    run_cmd, disp = build_and_get_runner(src_path)
    if not run_cmd:
        return

    tests_root = os.path.join(problem_folder, "tests")
    in_dir = os.path.join(tests_root, "in")
    out_dir = os.path.join(tests_root, "out")

    if os.path.isdir(in_dir) and os.path.isdir(out_dir):
        in_files = _sorted_files(in_dir)
        out_files = _sorted_files(out_dir)
    else:
        all_files = _sorted_files(tests_root)
        if not all_files:
            print("No test files found. Expected tests/in & tests/out or tests/*.")
            return
        in_files = [p for p in all_files if os.path.splitext(p)[1].lower() not in OUTPUT_EXTS]
        out_files = [p for p in all_files if os.path.splitext(p)[1].lower() in OUTPUT_EXTS]

    if not in_files:
        print("No input files found. (tips: use tests/in/* for any extensions)")
        return
    if not out_files:
        print("No output files found. (tips: use tests/out/* for any extensions)")
        return

    idx = _alpha_index_from_filename(src_filename)  # A=0, B=1, ...
    if idx >= len(in_files) or idx >= len(out_files):
        print(f"Not enough test files: need at least {idx+1}. "
              f"found {len(in_files)} inputs and {len(out_files)} outputs.")
        print("Inputs:")
        for i, p in enumerate(in_files, 1): print(f"  {i}. {os.path.basename(p)}")
        print("Outputs:")
        for i, p in enumerate(out_files, 1): print(f"  {i}. {os.path.basename(p)}")
        return

    in_path = in_files[idx]
    out_path = out_files[idx]

    with open(in_path, "r", encoding="utf-8") as f:
        input_data = f.read()
    with open(out_path, "r", encoding="utf-8") as f:
        expected_output = f.read()

    process = subprocess.run(run_cmd, input=input_data.encode(),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode != 0:
        print(f"Runtime error on {os.path.basename(in_path)}:\n{process.stderr.decode()}")
        return

    output = process.stdout.decode()
    _compare_and_report(src_filename, in_path, output, expected_output)


# ---------------- clangd (unchanged) ----------------
CLANGD_TEMPLATE = """CompileFlags:
  Add:
    - -std=gnu++17
    - -Wall
    - -Wextra
    - -Wpedantic
    - -isystem C:/msys64/mingw64/include
    - -isystem C:/msys64/mingw64/include/c++/13.2.0
    - -isystem C:/msys64/mingw64/include/c++/13.2.0/x86_64-w64-mingw32

"""

def write_clangd(directory: str):
    path = os.path.join(directory, ".clangd")
    if os.path.exists(path):
        print(f".clangd already exists: {path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(CLANGD_TEMPLATE)
    print(f"Created: {path}")

def write_compile_commands(directory: str):
    """
    Generate compile_commands.json for all *.cpp in `directory`.
    clangd will parse code exactly as g++ does (MinGW-safe).
    """
    root = Path(directory).resolve()
    cpp_files = sorted(p for p in root.glob("*.cpp"))

    include_flag = []
    if (root / "include").exists():
        include_flag = [f"-I{(root / 'include').as_posix()}"]

    entries = []
    for src in cpp_files:
        cmd_parts = [
            GPP,
            STD,
            *EXTRA_WARN,
            *include_flag,
            "-c",
            src.as_posix()
        ]
        entries.append({
            "directory": root.as_posix(),
            "file": src.as_posix(),
            "command": " ".join(cmd_parts)
        })

    out_path = root / "compile_commands.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)

    print(f"Wrote: {out_path} ({len(entries)} files)")

# ---------------- creators ----------------
def create_cpp_files(directory: str, num_files: int):
    os.makedirs(directory, exist_ok=True)
    include_dir = os.path.join(directory, "include")
    os.makedirs(include_dir, exist_ok=True)

    for i in range(num_files):
        filename = os.path.join(directory, f"{string.ascii_uppercase[i]}.cpp")
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write(CPP_TEMPLATE)
            print(f"Created: {filename}")
        else:
            print(f"File already exists: {filename}")

    write_compile_commands(directory)


def create_java_files(directory: str, num_files: int):
    os.makedirs(directory, exist_ok=True)
    for i in range(num_files):
        class_name = f"{string.ascii_uppercase[i]}"
        filename = os.path.join(directory, f"{class_name}.java")
        if not os.path.exists(filename):
            content = JAVA_TEMPLATE.replace("%CLASS%", class_name)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Created: {filename}")
        else:
            print(f"File already exists: {filename}")

# ---------------- legacy batch grade (kept) ----------------
def run_test_cases(problem_folder: str):
    """
    Batch grade for BOTH .cpp and .java.
    For each source file:
      - Build runner via build_and_get_runner()
      - Discover tests:
          * Preferred: <problem_folder>/tests/in/* and tests/out/*  (any extensions)
          * Fallback:  <problem_folder>/tests/* mixed; inputs = files NOT in OUTPUT_EXTS,
                       outputs = files IN OUTPUT_EXTS (.out/.ans/.expected)
      - Pick Nth input & Nth output by alphabetical order, where N is based on filename:
          A=1st, B=2nd, ...
    """
    # collect .cpp and .java
    src_files = [
        f for f in os.listdir(problem_folder)
        if f.lower().endswith(".cpp") or f.lower().endswith(".java")
    ]
    if not src_files:
        print("No .cpp or .java files found.")
        return

    tests_root = os.path.join(problem_folder, "tests")
    in_dir = os.path.join(tests_root, "in")
    out_dir = os.path.join(tests_root, "out")

    # prepare test lists once (shared for all problems)
    if os.path.isdir(in_dir) and os.path.isdir(out_dir):
        in_files_all = _sorted_files(in_dir)
        out_files_all = _sorted_files(out_dir)
        layout_hint = "tests/in + tests/out"
    else:
        all_files = _sorted_files(tests_root)
        if not all_files:
            print("No test files found. Expected tests/in & tests/out or tests/*.")
            return
        in_files_all  = [p for p in all_files if os.path.splitext(p)[1].lower() not in OUTPUT_EXTS]
        out_files_all = [p for p in all_files if os.path.splitext(p)[1].lower() in OUTPUT_EXTS]
        layout_hint = "mixed tests/ (ext-based split)"

    if not in_files_all:
        print(f"No input files found under {layout_hint}.")
        return
    if not out_files_all:
        print(f"No output files found under {layout_hint}.")
        return

    print(f"[grade] Using {layout_hint}: {len(in_files_all)} inputs, {len(out_files_all)} outputs.")

    for src_filename in sorted(src_files, key=str.lower):
        src_path = os.path.join(problem_folder, src_filename)
        run_cmd, disp = build_and_get_runner(src_path)
        if not run_cmd:
            continue

        try:
            idx = _alpha_index_from_filename(src_filename)  # A=0, B=1, ...
        except ValueError as e:
            print(f"Skip {src_filename}: {e}")
            continue

        if idx >= len(in_files_all) or idx >= len(out_files_all):
            print(f"[{src_filename}] Not enough tests (need {idx+1}). "
                  f"Found {len(in_files_all)} inputs / {len(out_files_all)} outputs.")
            continue

        in_path  = in_files_all[idx]
        out_path = out_files_all[idx]

        with open(in_path, "r", encoding="utf-8") as f:
            input_data = f.read()
        with open(out_path, "r", encoding="utf-8") as f:
            expected_output = f.read().strip()

        process = subprocess.run(run_cmd, input=input_data.encode(),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        tag = f"{os.path.basename(in_path)}"
        if process.returncode != 0:
            print(f"❌ {src_filename} runtime error on {tag}:\n{process.stderr.decode()}")
            continue

        output = process.stdout.decode()
        _compare_and_report(src_filename, in_path, output, expected_output)


# ---------------- CLI ----------------
def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python script.py create <directory> <num_files> [--lang cpp|java|both]")
        print("  python script.py grade")
        print("  python script.py testone <filename>")
        return

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 4:
            print("Usage: python script.py create <directory> <num_files> [--lang cpp|java|both]")
            return
        directory = sys.argv[2]
        num_files = int(sys.argv[3])
        lang = "cpp"
        if len(sys.argv) >= 6 and sys.argv[4] == "--lang":
            lang = sys.argv[5].lower()
        elif len(sys.argv) >= 5 and sys.argv[4].startswith("--lang"):
            lang = sys.argv[4].split("=", 1)[1].lower()

        if lang == "cpp":
            create_cpp_files(directory, num_files)
        elif lang == "java":
            create_java_files(directory, num_files)
        elif lang == "both":
            create_cpp_files(directory, num_files)
            create_java_files(directory, num_files)
        else:
            print("Unknown --lang value. Use cpp|java|both.")

    elif command == "grade":
        # use current working directory
        directory = os.getcwd()
        print(f"[grade] Using current directory: {directory}")
        run_test_cases(directory)

    elif command == "testone":
        if len(sys.argv) < 3:
            print("Usage: python script.py testone <filename>")
            return
        directory = os.getcwd()
        filename = sys.argv[2]
        print(f"[testone] Using current directory: {directory}")
        run_single_test(directory, filename)

    else:
        print("Invalid command. Use 'create', 'grade', or 'testone'.")

if __name__ == "__main__":
    main()
