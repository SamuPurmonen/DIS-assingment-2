"""
Library Management System - Console UI
Three SQLite databases: books.db, members.db, transactions.db
Run: python library.py
Type 'q' at any prompt to cancel and go back.
"""

import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "databases")
os.makedirs(DB_DIR, exist_ok=True)

def get_db(name):
    con = sqlite3.connect(os.path.join(DB_DIR, f"{name}.db"))
    con.row_factory = sqlite3.Row
    return con

def setup():
    con = get_db("books")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title     TEXT    NOT NULL,
            author    TEXT    NOT NULL,
            genre     TEXT    DEFAULT 'General',
            year      INTEGER,
            copies    INTEGER DEFAULT 1,
            available INTEGER DEFAULT 1
        );
    """)
    if con.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
        con.executemany(
            "INSERT INTO books (title,author,genre,year,copies,available) VALUES (?,?,?,?,?,?)",
            [
                ("The Great Gatsby",       "F. Scott Fitzgerald", "Classic",     1925, 3, 3),
                ("1984",                   "George Orwell",       "Dystopian",   1949, 4, 3),
                ("Dune",                   "Frank Herbert",       "Sci-Fi",      1965, 2, 1),
                ("The Hobbit",             "J.R.R. Tolkien",      "Fantasy",     1937, 3, 3),
                ("Brave New World",        "Aldous Huxley",       "Dystopian",   1932, 2, 2),
                ("The Catcher in the Rye", "J.D. Salinger",       "Classic",     1951, 1, 0),
                ("Foundation",             "Isaac Asimov",        "Sci-Fi",      1951, 3, 3),
                ("The Alchemist",          "Paulo Coelho",        "Fiction",     1988, 2, 2),
                ("Sapiens",                "Yuval Noah Harari",   "Non-Fiction", 2011, 3, 3),
                ("The Martian",            "Andy Weir",           "Sci-Fi",      2011, 2, 2),
            ]
        )
        con.commit()
    con.close()

    con = get_db("members")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS members (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            email     TEXT UNIQUE NOT NULL,
            phone     TEXT,
            join_date TEXT DEFAULT (date('now')),
            active    INTEGER DEFAULT 1
        );
    """)
    if con.execute("SELECT COUNT(*) FROM members").fetchone()[0] == 0:
        con.executemany(
            "INSERT INTO members (name,email,phone,join_date,active) VALUES (?,?,?,?,?)",
            [
                ("Alice Johnson", "alice@example.com", "555-0101", "2024-01-15", 1),
                ("Bob Smith",     "bob@example.com",   "555-0102", "2024-02-20", 1),
                ("Carol White",   "carol@example.com", "555-0103", "2024-03-10", 1),
                ("David Brown",   "david@example.com", "555-0104", "2024-04-05", 1),
                ("Eva Martinez",  "eva@example.com",   "555-0105", "2024-05-18", 1),
                ("Frank Wilson",  "frank@example.com", "555-0106", "2024-06-22", 0),
                ("Grace Lee",     "grace@example.com", "555-0107", "2024-07-30", 1),
                ("Henry Davis",   "henry@example.com", "555-0108", "2024-08-14", 1),
            ]
        )
        con.commit()
    con.close()

    con = get_db("transactions")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id     INTEGER NOT NULL,
            member_id   INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            due_date    TEXT NOT NULL,
            return_date TEXT,
            status      TEXT DEFAULT 'borrowed'
        );
    """)
    if con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 0:
        con.executemany(
            "INSERT INTO transactions (book_id,member_id,borrow_date,due_date,return_date,status) VALUES (?,?,?,?,?,?)",
            [
                (1, 1, "2026-09-01", "2026-09-15", "2026-09-14", "returned"),
                (3, 2, "2026-09-10", "2026-09-24", None,          "overdue"),
                (2, 3, "2026-10-01", "2026-10-15", None,          "borrowed"),
                (4, 4, "2026-10-05", "2026-10-19", None,          "borrowed"),
                (6, 1, "2026-10-10", "2026-10-24", None,          "overdue"),
                (7, 5, "2026-09-20", "2026-10-04", "2026-10-03", "returned"),
                (9, 6, "2026-10-12", "2026-10-26", None,          "borrowed"),
            ]
        )
        con.commit()
    con.close()


# ─── exceptions ────────────────────────────────────────────────────────────────

class Cancel(Exception):
    pass


# ─── display helpers ───────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def hr(char="─", width=60):
    print(char * width)

def header(title):
    hr("═")
    print(f"  {title}")
    print(f"  (type 'q' at any prompt to cancel / go back)")
    hr("═")

def pause():
    input("\n  Press Enter to continue...")

def prompt(msg, default=None):
    suffix = f" [{default}]" if default is not None else ""
    val = input(f"  {msg}{suffix}: ").strip()
    if val.lower() == "q":
        raise Cancel()
    return val if val != "" else (str(default) if default is not None else "")

def prompt_int(msg, default=None):
    while True:
        val = prompt(msg, default)
        try:
            return int(val)
        except ValueError:
            print("  Please enter a number (or 'q' to cancel).")

def confirm(msg):
    try:
        return prompt(f"{msg} (y/n)", "n").lower() == "y"
    except Cancel:
        return False

def print_table(rows, cols, widths):
    hr()
    print("  " + "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(cols)))
    hr()
    if not rows:
        print("  (no records found)")
    for row in rows:
        vals = row if isinstance(row, dict) else dict(row)
        print("  " + "  ".join(
            str(vals.get(c, "") if vals.get(c) is not None else "—").ljust(widths[i])
            for i, c in enumerate(cols)
        ))
    hr()
    print(f"  {len(rows)} record(s)")

def show_book(row):
    """Print a single book summary box."""
    hr()
    print(f"  ID        : {row['id']}")
    print(f"  Title     : {row['title']}")
    print(f"  Author    : {row['author']}")
    print(f"  Genre     : {row['genre']}")
    print(f"  Year      : {row['year'] or '—'}")
    print(f"  Copies    : {row['copies']}  (available: {row['available']})")
    hr()

def show_member(row):
    """Print a single member summary box."""
    hr()
    print(f"  ID        : {row['id']}")
    print(f"  Name      : {row['name']}")
    print(f"  Email     : {row['email']}")
    print(f"  Phone     : {row['phone'] or '—'}")
    print(f"  Joined    : {row['join_date']}")
    print(f"  Active    : {'Yes' if row['active'] else 'No'}")
    hr()

def show_transaction(row):
    """Print a single transaction summary box (enriched with book/member names)."""
    enriched = enrich([row])[0]
    hr()
    print(f"  ID        : {enriched['id']}")
    print(f"  Book      : {enriched['book']}  (ID {enriched['book_id']})")
    print(f"  Member    : {enriched['member']}  (ID {enriched['member_id']})")
    print(f"  Borrowed  : {enriched['borrow_date']}")
    print(f"  Due       : {enriched['due_date']}")
    print(f"  Returned  : {enriched['return_date'] or '—'}")
    print(f"  Status    : {enriched['status']}")
    hr()


# ─── books ─────────────────────────────────────────────────────────────────────

def books_menu():
    while True:
        clear()
        header("DATABASE: books.db  |  Books Catalogue")
        print("  1. List all books")
        print("  2. Search books")
        print("  3. View book detail")
        print("  4. Add book")
        print("  5. Edit book")
        print("  6. Delete book")
        print("  0. Back")
        hr()
        choice = prompt("Choice")
        if   choice == "1": books_list()
        elif choice == "2": books_search()
        elif choice == "3": books_view()
        elif choice == "4": books_add()
        elif choice == "5": books_edit()
        elif choice == "6": books_delete()
        elif choice == "0": break
        else:
            print("  Invalid choice.")
            pause()

def books_list():
    clear()
    header("Books — All Records")
    con  = get_db("books")
    rows = con.execute("SELECT * FROM books ORDER BY title").fetchall()
    con.close()
    print_table(rows, ["id","title","author","genre","year","copies","available"],
                       [4, 26, 22, 12, 6, 7, 9])
    pause()

def books_search():
    clear()
    header("Books — Search")
    try:
        term = prompt("Search (title / author / genre)")
    except Cancel:
        return
    like = f"%{term}%"
    con  = get_db("books")
    rows = con.execute(
        "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR genre LIKE ? ORDER BY title",
        (like, like, like)
    ).fetchall()
    con.close()
    print_table(rows, ["id","title","author","genre","year","copies","available"],
                       [4, 26, 22, 12, 6, 7, 9])
    pause()

def books_view():
    clear()
    header("Books — Detail")
    try:
        bid = prompt_int("Book ID")
    except Cancel:
        return
    con = get_db("books")
    row = con.execute("SELECT * FROM books WHERE id=?", (bid,)).fetchone()
    con.close()
    if not row:
        print("  Not found.")
    else:
        show_book(row)
    pause()

def books_add():
    clear()
    header("Books — Add")
    try:
        title  = prompt("Title")
        author = prompt("Author")
        genre  = prompt("Genre", "General")
        year   = prompt("Year (blank to skip)", "")
        copies = prompt_int("Copies", 1)
    except Cancel:
        print("  Cancelled.")
        pause()
        return
    year = int(year) if year.isdigit() else None
    con  = get_db("books")
    con.execute(
        "INSERT INTO books (title,author,genre,year,copies,available) VALUES (?,?,?,?,?,?)",
        (title, author, genre, year, copies, copies)
    )
    con.commit()
    con.close()
    print(f"\n  '{title}' added.")
    pause()

def books_edit():
    clear()
    header("Books — Edit  |  Choose from list below")

    # Show full list first
    con  = get_db("books")
    rows = con.execute("SELECT * FROM books ORDER BY title").fetchall()
    con.close()
    print_table(rows, ["id","title","author","genre","year","copies","available"],
                       [4, 26, 22, 12, 6, 7, 9])

    try:
        bid = prompt_int("Book ID to edit")
    except Cancel:
        return

    con = get_db("books")
    row = con.execute("SELECT * FROM books WHERE id=?", (bid,)).fetchone()
    if not row:
        con.close()
        print("  Not found.")
        pause()
        return

    print("\n  Current values shown in brackets — press Enter to keep, or type new value:\n")
    show_book(row)

    try:
        title     = prompt("Title",     row["title"])
        author    = prompt("Author",    row["author"])
        genre     = prompt("Genre",     row["genre"])
        year      = prompt("Year",      row["year"] or "")
        copies    = prompt_int("Copies",    row["copies"])
        available = prompt_int("Available", row["available"])
    except Cancel:
        con.close()
        print("  Cancelled.")
        pause()
        return

    year = int(year) if str(year).isdigit() else None
    con.execute(
        "UPDATE books SET title=?,author=?,genre=?,year=?,copies=?,available=? WHERE id=?",
        (title, author, genre, year, copies, available, bid)
    )
    con.commit()

    print("\n  Updated record:")
    row = con.execute("SELECT * FROM books WHERE id=?", (bid,)).fetchone()
    show_book(row)
    con.close()
    pause()

def books_delete():
    clear()
    header("Books — Delete  |  Choose from list below")

    # Show full list first
    con  = get_db("books")
    rows = con.execute("SELECT * FROM books ORDER BY title").fetchall()
    con.close()
    print_table(rows, ["id","title","author","genre","year","copies","available"],
                       [4, 26, 22, 12, 6, 7, 9])

    try:
        bid = prompt_int("Book ID to delete")
    except Cancel:
        return

    con = get_db("books")
    row = con.execute("SELECT * FROM books WHERE id=?", (bid,)).fetchone()
    if not row:
        con.close()
        print("  Not found.")
        pause()
        return

    print("\n  You are about to delete this record:")
    show_book(row)

    if confirm("Permanently delete this book?"):
        con.execute("DELETE FROM books WHERE id=?", (bid,))
        con.commit()
        print("  Deleted.")
    else:
        print("  Cancelled.")
    con.close()
    pause()


# ─── members ───────────────────────────────────────────────────────────────────

def members_menu():
    while True:
        clear()
        header("DATABASE: members.db  |  Members Directory")
        print("  1. List all members")
        print("  2. Search members")
        print("  3. View member detail")
        print("  4. Add member")
        print("  5. Edit member")
        print("  6. Delete member")
        print("  0. Back")
        hr()
        choice = prompt("Choice")
        if   choice == "1": members_list()
        elif choice == "2": members_search()
        elif choice == "3": members_view()
        elif choice == "4": members_add()
        elif choice == "5": members_edit()
        elif choice == "6": members_delete()
        elif choice == "0": break
        else:
            print("  Invalid choice.")
            pause()

def members_list():
    clear()
    header("Members — All Records")
    con  = get_db("members")
    rows = con.execute("SELECT * FROM members ORDER BY name").fetchall()
    con.close()
    print_table(rows, ["id","name","email","phone","join_date","active"],
                       [4, 18, 24, 12, 12, 7])
    pause()

def members_search():
    clear()
    header("Members — Search")
    try:
        term = prompt("Search (name / email)")
    except Cancel:
        return
    like = f"%{term}%"
    con  = get_db("members")
    rows = con.execute(
        "SELECT * FROM members WHERE name LIKE ? OR email LIKE ? ORDER BY name",
        (like, like)
    ).fetchall()
    con.close()
    print_table(rows, ["id","name","email","phone","join_date","active"],
                       [4, 18, 24, 12, 12, 7])
    pause()

def members_view():
    clear()
    header("Members — Detail")
    try:
        mid = prompt_int("Member ID")
    except Cancel:
        return
    con = get_db("members")
    row = con.execute("SELECT * FROM members WHERE id=?", (mid,)).fetchone()
    con.close()
    if not row:
        print("  Not found.")
    else:
        show_member(row)
    pause()

def members_add():
    clear()
    header("Members — Add")
    try:
        name  = prompt("Full name")
        email = prompt("Email")
        phone = prompt("Phone (blank to skip)", "") or None
    except Cancel:
        print("  Cancelled.")
        pause()
        return
    con = get_db("members")
    try:
        con.execute(
            "INSERT INTO members (name,email,phone,join_date,active) VALUES (?,?,?,date('now'),1)",
            (name, email, phone)
        )
        con.commit()
        print(f"\n  '{name}' added.")
    except sqlite3.IntegrityError:
        print(f"\n  Error: email '{email}' already exists.")
    con.close()
    pause()

def members_edit():
    clear()
    header("Members — Edit  |  Choose from list below")

    con  = get_db("members")
    rows = con.execute("SELECT * FROM members ORDER BY name").fetchall()
    con.close()
    print_table(rows, ["id","name","email","phone","join_date","active"],
                       [4, 18, 24, 12, 12, 7])

    try:
        mid = prompt_int("Member ID to edit")
    except Cancel:
        return

    con = get_db("members")
    row = con.execute("SELECT * FROM members WHERE id=?", (mid,)).fetchone()
    if not row:
        con.close()
        print("  Not found.")
        pause()
        return

    print("\n  Current values shown in brackets — press Enter to keep, or type new value:\n")
    show_member(row)

    try:
        name   = prompt("Name",  row["name"])
        email  = prompt("Email", row["email"])
        phone  = prompt("Phone", row["phone"] or "") or None
        active = prompt_int("Active (1=yes 0=no)", row["active"])
    except Cancel:
        con.close()
        print("  Cancelled.")
        pause()
        return

    try:
        con.execute(
            "UPDATE members SET name=?,email=?,phone=?,active=? WHERE id=?",
            (name, email, phone, active, mid)
        )
        con.commit()
        print("\n  Updated record:")
        row = con.execute("SELECT * FROM members WHERE id=?", (mid,)).fetchone()
        show_member(row)
    except sqlite3.IntegrityError:
        print(f"\n  Error: email '{email}' already exists.")
    con.close()
    pause()

def members_delete():
    clear()
    header("Members — Delete  |  Choose from list below")

    con  = get_db("members")
    rows = con.execute("SELECT * FROM members ORDER BY name").fetchall()
    con.close()
    print_table(rows, ["id","name","email","phone","join_date","active"],
                       [4, 18, 24, 12, 12, 7])

    try:
        mid = prompt_int("Member ID to delete")
    except Cancel:
        return

    con = get_db("members")
    row = con.execute("SELECT * FROM members WHERE id=?", (mid,)).fetchone()
    if not row:
        con.close()
        print("  Not found.")
        pause()
        return

    print("\n  You are about to delete this record:")
    show_member(row)

    if confirm("Permanently delete this member?"):
        con.execute("DELETE FROM members WHERE id=?", (mid,))
        con.commit()
        print("  Deleted.")
    else:
        print("  Cancelled.")
    con.close()
    pause()


# ─── transactions ──────────────────────────────────────────────────────────────

def enrich(rows):
    cb = get_db("books")
    cm = get_db("members")
    out = []
    for r in rows:
        d = dict(r)
        b = cb.execute("SELECT title FROM books   WHERE id=?", (d["book_id"],)).fetchone()
        m = cm.execute("SELECT name  FROM members WHERE id=?", (d["member_id"],)).fetchone()
        d["book"]   = b["title"] if b else f"#{d['book_id']}"
        d["member"] = m["name"]  if m else f"#{d['member_id']}"
        out.append(d)
    cb.close()
    cm.close()
    return out

def transactions_menu():
    while True:
        clear()
        header("DATABASE: transactions.db  |  Transactions Log")
        print("  1. List all transactions")
        print("  2. Filter by status")
        print("  3. View transaction detail")
        print("  4. Borrow a book")
        print("  5. Return a book")
        print("  6. Edit transaction")
        print("  7. Delete transaction")
        print("  0. Back")
        hr()
        choice = prompt("Choice")
        if   choice == "1": transactions_list()
        elif choice == "2": transactions_by_status()
        elif choice == "3": transactions_view()
        elif choice == "4": transactions_borrow()
        elif choice == "5": transactions_return()
        elif choice == "6": transactions_edit()
        elif choice == "7": transactions_delete()
        elif choice == "0": break
        else:
            print("  Invalid choice.")
            pause()

def transactions_list(status=None):
    clear()
    title = f"Transactions — {status.capitalize()}" if status else "Transactions — All"
    header(title)
    con = get_db("transactions")
    if status:
        rows = con.execute(
            "SELECT * FROM transactions WHERE status=? ORDER BY borrow_date DESC", (status,)
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT * FROM transactions ORDER BY borrow_date DESC"
        ).fetchall()
    con.close()
    rows = enrich(rows)
    hr()
    print(f"  {'ID':<4}  {'Book':<26}  {'Member':<18}  {'Borrowed':<12}  {'Due':<12}  {'Status'}")
    hr()
    if not rows:
        print("  (no records found)")
    for r in rows:
        print(f"  {r['id']:<4}  {r['book'][:25]:<26}  {r['member'][:17]:<18}  "
              f"{r['borrow_date']:<12}  {r['due_date']:<12}  {r['status']}")
    hr()
    print(f"  {len(rows)} record(s)")
    pause()

def transactions_by_status():
    clear()
    header("Transactions — Filter by Status")
    try:
        status = prompt("Status (borrowed / returned / overdue)")
    except Cancel:
        return
    if status not in ("borrowed", "returned", "overdue"):
        print("  Invalid status.")
        pause()
        return
    transactions_list(status)

def transactions_view():
    clear()
    header("Transactions — Detail")
    try:
        tid = prompt_int("Transaction ID")
    except Cancel:
        return
    con = get_db("transactions")
    row = con.execute("SELECT * FROM transactions WHERE id=?", (tid,)).fetchone()
    con.close()
    if not row:
        print("  Not found.")
        pause()
        return
    show_transaction(row)
    pause()

def transactions_borrow():
    clear()
    header("Transactions — Borrow a Book")
    cb    = get_db("books")
    books = cb.execute(
        "SELECT id,title,available FROM books WHERE available>0 ORDER BY title"
    ).fetchall()
    cb.close()
    if not books:
        print("  No books currently available.")
        pause()
        return
    print("  Available books:\n")
    for b in books:
        print(f"  [{b['id']}]  {b['title']}  (available: {b['available']})")
    print()
    try:
        book_id = prompt_int("Book ID (or 'q' to cancel)")
    except Cancel:
        return
    cb   = get_db("books")
    book = cb.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not book or book["available"] < 1:
        cb.close()
        print("  Not available.")
        pause()
        return
    cm      = get_db("members")
    members = cm.execute(
        "SELECT id,name FROM members WHERE active=1 ORDER BY name"
    ).fetchall()
    cm.close()
    print()
    for m in members:
        print(f"  [{m['id']}]  {m['name']}")
    print()
    try:
        member_id = prompt_int("Member ID (or 'q' to cancel)")
        due_date  = prompt("Due date (YYYY-MM-DD)")
    except Cancel:
        cb.close()
        print("  Cancelled.")
        pause()
        return
    cm     = get_db("members")
    member = cm.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone()
    cm.close()
    if not member:
        cb.close()
        print("  Member not found.")
        pause()
        return
    ct = get_db("transactions")
    ct.execute(
        "INSERT INTO transactions (book_id,member_id,borrow_date,due_date,status) "
        "VALUES (?,?,date('now'),?,'borrowed')",
        (book_id, member_id, due_date)
    )
    ct.commit()
    ct.close()
    cb.execute("UPDATE books SET available=available-1 WHERE id=?", (book_id,))
    cb.commit()
    cb.close()
    print(f"\n  '{book['title']}' borrowed by {member['name']}. Due: {due_date}")
    pause()

def transactions_return():
    clear()
    header("Transactions — Return a Book")
    ct   = get_db("transactions")
    rows = ct.execute(
        "SELECT * FROM transactions WHERE status IN ('borrowed','overdue') ORDER BY due_date"
    ).fetchall()
    ct.close()
    enriched = enrich(rows)
    if not enriched:
        print("  No active borrows.")
        pause()
        return
    print("  Active borrows:\n")
    for r in enriched:
        print(f"  [{r['id']}]  {r['book'][:30]}  —  {r['member']}  (due {r['due_date']})")
    print()
    try:
        tid = prompt_int("Transaction ID to return (or 'q' to cancel)")
    except Cancel:
        return
    ct  = get_db("transactions")
    row = ct.execute("SELECT * FROM transactions WHERE id=?", (tid,)).fetchone()
    if not row or row["status"] not in ("borrowed", "overdue"):
        ct.close()
        print("  Not found or already returned.")
        pause()
        return
    ct.execute(
        "UPDATE transactions SET status='returned', return_date=date('now') WHERE id=?", (tid,)
    )
    ct.commit()
    ct.close()
    cb = get_db("books")
    cb.execute("UPDATE books SET available=available+1 WHERE id=?", (row["book_id"],))
    cb.commit()
    cb.close()
    print("  Marked as returned.")
    pause()

def transactions_edit():
    clear()
    header("Transactions — Edit  |  Choose from list below")

    con  = get_db("transactions")
    rows = con.execute("SELECT * FROM transactions ORDER BY borrow_date DESC").fetchall()
    con.close()
    enriched = enrich(rows)
    hr()
    print(f"  {'ID':<4}  {'Book':<26}  {'Member':<18}  {'Borrowed':<12}  {'Due':<12}  {'Status'}")
    hr()
    if not enriched:
        print("  (no records found)")
    for r in enriched:
        print(f"  {r['id']:<4}  {r['book'][:25]:<26}  {r['member'][:17]:<18}  "
              f"{r['borrow_date']:<12}  {r['due_date']:<12}  {r['status']}")
    hr()

    try:
        tid = prompt_int("Transaction ID to edit")
    except Cancel:
        return

    ct  = get_db("transactions")
    row = ct.execute("SELECT * FROM transactions WHERE id=?", (tid,)).fetchone()
    if not row:
        ct.close()
        print("  Not found.")
        pause()
        return

    print("\n  Current values shown in brackets — press Enter to keep, or type new value:\n")
    show_transaction(row)

    old_status = row["status"]
    try:
        due_date    = prompt("Due date",    row["due_date"])
        status      = prompt("Status (borrowed/returned/overdue)", old_status)
        return_date = prompt("Return date (YYYY-MM-DD, blank=none)", row["return_date"] or "") or None
    except Cancel:
        ct.close()
        print("  Cancelled.")
        pause()
        return

    ct.execute(
        "UPDATE transactions SET due_date=?,status=?,return_date=? WHERE id=?",
        (due_date, status, return_date, tid)
    )
    ct.commit()

    print("\n  Updated record:")
    row = ct.execute("SELECT * FROM transactions WHERE id=?", (tid,)).fetchone()
    show_transaction(row)
    ct.close()

    was_out = old_status in ("borrowed", "overdue")
    now_out = status     in ("borrowed", "overdue")
    cb = get_db("books")
    if was_out and not now_out:
        cb.execute("UPDATE books SET available=available+1 WHERE id=?", (row["book_id"],))
    elif not was_out and now_out:
        cb.execute("UPDATE books SET available=available-1 WHERE id=?", (row["book_id"],))
    cb.commit()
    cb.close()
    pause()

def transactions_delete():
    clear()
    header("Transactions — Delete  |  Choose from list below")

    con  = get_db("transactions")
    rows = con.execute("SELECT * FROM transactions ORDER BY borrow_date DESC").fetchall()
    con.close()
    enriched = enrich(rows)
    hr()
    print(f"  {'ID':<4}  {'Book':<26}  {'Member':<18}  {'Borrowed':<12}  {'Due':<12}  {'Status'}")
    hr()
    if not enriched:
        print("  (no records found)")
    for r in enriched:
        print(f"  {r['id']:<4}  {r['book'][:25]:<26}  {r['member'][:17]:<18}  "
              f"{r['borrow_date']:<12}  {r['due_date']:<12}  {r['status']}")
    hr()

    try:
        tid = prompt_int("Transaction ID to delete")
    except Cancel:
        return

    ct  = get_db("transactions")
    row = ct.execute("SELECT * FROM transactions WHERE id=?", (tid,)).fetchone()
    if not row:
        ct.close()
        print("  Not found.")
        pause()
        return

    print("\n  You are about to delete this record:")
    show_transaction(row)

    if confirm("Permanently delete this transaction?"):
        ct.execute("DELETE FROM transactions WHERE id=?", (tid,))
        ct.commit()
        if row["status"] in ("borrowed", "overdue"):
            cb = get_db("books")
            cb.execute("UPDATE books SET available=available+1 WHERE id=?", (row["book_id"],))
            cb.commit()
            cb.close()
        print("  Deleted.")
    else:
        print("  Cancelled.")
    ct.close()
    pause()


# ─── main menu ─────────────────────────────────────────────────────────────────

def stats():
    cb = get_db("books")
    cm = get_db("members")
    ct = get_db("transactions")
    tb = cb.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    ab = cb.execute("SELECT COALESCE(SUM(available),0) FROM books").fetchone()[0]
    tm = cm.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    bo = ct.execute("SELECT COUNT(*) FROM transactions WHERE status='borrowed'").fetchone()[0]
    ov = ct.execute("SELECT COUNT(*) FROM transactions WHERE status='overdue'").fetchone()[0]
    cb.close(); cm.close(); ct.close()
    return tb, ab, tm, bo, ov

def main():
    setup()
    while True:
        clear()
        tb, ab, tm, bo, ov = stats()
        hr("═")
        print("  LIBRARY MANAGEMENT SYSTEM")
        hr("═")
        print(f"  Books: {tb} total, {ab} available  |  Members: {tm}  |  Borrowed: {bo}  |  Overdue: {ov}")
        hr()
        print("  Select a database:\n")
        print("  1.  books.db         — Books catalogue")
        print("  2.  members.db       — Library members")
        print("  3.  transactions.db  — Borrow / return records")
        print("  0.  Quit")
        hr()
        try:
            choice = prompt("Choice")
        except Cancel:
            continue
        if   choice == "1": books_menu()
        elif choice == "2": members_menu()
        elif choice == "3": transactions_menu()
        elif choice == "0":
            clear()
            print("  Goodbye.\n")
            break
        else:
            print("  Invalid choice.")
            pause()

if __name__ == "__main__":
    main()
