# dump_to_DB.py  (overwrite file at C:\Users\shrey\Desktop\HCLTech_hackathon\dump_to_DB.py)
import os, re, sqlite3
from datetime import datetime

DUMP_PATH = r"C:\Users\shrey\Desktop\HCLTech_hackathon\meteodb_export.sql"
DB_PATH   = r"C:\Users\shrey\Desktop\HCLTech_hackathon\meteodb.db"
FAILED_SQL = r"C:\Users\shrey\Desktop\HCLTech_hackathon\failed_statements.sql"

if not os.path.exists(DUMP_PATH):
    raise FileNotFoundError(DUMP_PATH + " not found")

raw = open(DUMP_PATH, "r", encoding="utf-8", errors="ignore").read()
raw = raw.replace("\r\n", "\n").replace("\r", "\n")

# Remove MySQL conditional comments /*! ... */
raw = re.sub(r"/\*![\s\S]*?\*/", "", raw)

# Remove SET/USE/LOCK/UNLOCK and single-line comments
raw = re.sub(r"(?m)^\s*(SET |USE |LOCK TABLES|UNLOCK TABLES).*$", "", raw)
raw = re.sub(r"(?m)^\s*--.*$", "", raw)
raw = re.sub(r"(?m)^\s*#.*$", "", raw)

# Aggressively remove COLLATE/CHARSET/ENGINE fragments anywhere
raw = re.sub(r"(?i)\s+COLLATE\s+[\w\d_]+\b", "", raw)
raw = re.sub(r"(?i)COLLATE\s*=\s*[\w\d_]+\b", "", raw)
raw = re.sub(r"(?i)CHARACTER SET\s*=\s*[\w\d_]+\b", "", raw)
raw = re.sub(r"(?i)DEFAULT\s+CHARSET\s*=\s*[\w\d_]+\b", "", raw)
raw = re.sub(r"(?i)\bCHARSET\s*=\s*[\w\d_]+\b", "", raw)
raw = re.sub(r"(?i)ENGINE\s*=\s*\w+\b", "", raw)

# Replace MySQL types with SQLite-friendly ones
raw = re.sub(r"(?i)\btinyint\b", "integer", raw)
raw = re.sub(r"(?i)\bint\(\d+\)\b", "integer", raw)
raw = re.sub(r"(?i)\bunsigned\b", "", raw)
raw = re.sub(r"(?i)\bdouble\b", "real", raw)
raw = re.sub(r"(?i)\bfloat\b", "real", raw)
raw = re.sub(r"(?i)\bdecimal\s*\([^\)]*\)", "real", raw)
raw = re.sub(r"(?i)\bjson\b", "text", raw)
raw = re.sub(r"(?i)\benum\s*\([^\)]*\)", "text", raw)
raw = re.sub(r"(?i)\bAUTO_INCREMENT\b", "", raw)

# Remove backticks
raw = raw.replace("`", "")

# Convert JSON-like {"en":"Name"...} to 'Name' (again, looser)
raw = re.sub(r"\{\s*['\"]?en['\"]?\s*:\s*['\"]([^'\"]+)['\"][^\}]*\}", r"'\1'", raw)

# ----- NEW: Remove REFERENCES / ON DELETE / ON UPDATE / GENERATED / CHECK -----
# Remove REFERENCES <anything in parentheses> optionally followed by ON DELETE/ON UPDATE(...)
raw = re.sub(r"(?is)\bREFERENCES\b\s+[^\s,(]+\s*\([^\)]*\)\s*(ON\s+DELETE\s+\w+(\s+ON\s+UPDATE\s+\w+)?)?", "", raw)

# Remove standalone ON DELETE ... and ON UPDATE ... that may appear after column definitions
raw = re.sub(r"(?i)\s+ON\s+DELETE\s+\w+\b", "", raw)
raw = re.sub(r"(?i)\s+ON\s+UPDATE\s+\w+\b", "", raw)

# Remove GENERATED ALWAYS AS (...) STORED / AS (...) VIRTUAL patterns
raw = re.sub(r"(?is)\bGENERATED\s+ALWAYS\s+AS\s*\([^\)]+\)\s*(STORED|VIRTUAL)?", "", raw)
raw = re.sub(r"(?is)\bAS\s*\([^\)]+\)\s*(STORED|VIRTUAL)?", "", raw)

# Remove CHECK(...) constraints entirely (can be inside column or after)
raw = re.sub(r"(?is)\bCHECK\s*\([^\)]*\)", "", raw)

# Also remove any leftover "USING BTREE" or "USING HASH" in index definitions
raw = re.sub(r"(?i)\bUSING\s+(BTREE|HASH)\b", "", raw)

# ----- End of new aggressive removals -----

# Extract CREATE TABLE blocks
create_blocks = [m.group(0) for m in re.finditer(r"(?is)(CREATE\s+TABLE\s+.*?\)\s*;)", raw)]

# Remove CREATE blocks from remaining SQL (so INSERTs stay)
remaining = raw
for blk in create_blocks:
    remaining = remaining.replace(blk, "")

def clean_create(blk):
    lines = blk.split("\n")
    out = []
    for ln in lines:
        ls = ln.strip()
        if not ls:
            continue
        # skip KEY/INDEX/UNIQUE KEY/CONSTRAINT/FOREIGN KEY lines
        if re.match(r"(?i)^(KEY|INDEX|UNIQUE KEY|CONSTRAINT|FOREIGN KEY)\b", ls):
            continue
        # skip leftover table options or weird fragments
        if re.match(r"(?i)^(ENGINE|DEFAULT CHARSET|CHARSET|COLLATE)\b", ls):
            continue
        # skip SET/LOCK/UNLOCK lines
        if re.match(r"(?i)^(SET |LOCK TABLES|UNLOCK TABLES|USE )", ls):
            continue
        out.append(ln.rstrip())
    cleaned = "\n".join(out)
    cleaned = re.sub(r",\s*\n\s*\)", "\n)", cleaned, flags=re.DOTALL)
    if not cleaned.strip().endswith(";"):
        cleaned = cleaned.strip() + ";\n"
    m = re.search(r"(?i)CREATE\s+TABLE\s+([^\s(]+)", cleaned)
    if m:
        tbl = m.group(1)
        cleaned = f"DROP TABLE IF EXISTS {tbl};\n{cleaned}"
    return cleaned

cleaned_creates = [clean_create(b) for b in create_blocks]

# Run CREATEs
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
create_fail = []
create_ok = 0
for i, stmt in enumerate(cleaned_creates, 1):
    try:
        cur.executescript(stmt)
        conn.commit()
        create_ok += 1
        print(f"  ✓ CREATE #{i} OK")
    except Exception as e:
        create_fail.append((stmt, str(e)))
        print(f"  ✖ CREATE #{i} failed -> {e}")

# Prepare INSERTs (clean escapes again)
ins_text = remaining.replace("\\'", "''").replace('\\\\', '\\')
ins_text = re.sub(r"\{\s*['\"]?en['\"]?\s*:\s*['\"]([^'\"]+)['\"][^\}]*\}", r"'\1'", ins_text)

insert_blocks = [m.group(0) for m in re.finditer(r"(?is)(INSERT\s+INTO\s+.*?;)", ins_text)]
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

insert_ok = 0
insert_fail = []
for idx, ins in enumerate(insert_blocks, 1):
    if not ins.strip():
        continue
    m = re.match(r"(?i)INSERT\s+INTO\s+([^\s(]+)", ins)
    target = m.group(1) if m else None
    if target and target not in tables:
        insert_fail.append((ins, f"missing table '{target}'"))
        print(f"  [WARN] INSERT #{idx} skipped - table '{target}' missing")
        continue
    try:
        cur.executescript(ins)
        conn.commit()
        insert_ok += 1
    except Exception as e:
        insert_fail.append((ins, str(e)))
        print(f"  [WARN] INSERT #{idx} failed -> {e}")

conn.close()

# Write failures to file
all_failed = create_fail + insert_fail
print(f"\n[SUMMARY] CREATE ok: {create_ok}, CREATE fail: {len(create_fail)}")
print(f"[SUMMARY] INSERT ok: {insert_ok}, INSERT fail/skipped: {len(insert_fail)}")

if all_failed:
    with open(FAILED_SQL, "w", encoding="utf-8") as f:
        f.write(f"-- Failed statements at {datetime.utcnow().isoformat()} UTC\n\n")
        for i, (stmt, err) in enumerate(all_failed, 1):
            f.write(f"-- FAIL #{i}: {err}\n")
            f.write(stmt.strip())
            if not stmt.strip().endswith(";"):
                f.write(";\n")
            f.write("\n\n")
    print(f"[INFO] {len(all_failed)} failing statements saved to: {FAILED_SQL}")
else:
    print("[SUCCESS] All executed cleanly")

print("[DONE] SQLite DB:", DB_PATH)
