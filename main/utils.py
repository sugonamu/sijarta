# utils.py
import psycopg2
from django.conf import settings

def get_db_connection():
    return psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT']
    )

def get_user_profile(request):
    # This assumes request.user.username is stored as users.PhoneNum
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.Id, u.Name, u.PhoneNum, u.MyPayBalance,
               (SELECT 'user' FROM sijarta.customer WHERE Id = u.Id LIMIT 1) AS is_user,
               (SELECT 'worker' FROM sijarta.worker WHERE Id = u.Id LIMIT 1) AS is_worker
        FROM sijarta.users u
        WHERE u.PhoneNum = %s
        LIMIT 1;
    """, [request.user.username])
    row = cursor.fetchone()
    conn.close()
    if row:
        role = 'worker' if row[5] == 'worker' else 'user' if row[4] == 'user' else None
        return {
            'id': row[0],
            'name': row[1],
            'phone': row[2],
            'mypay_balance': row[3],
            'role': role
        }
    return None


def authenticate_user(username, password):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.Id,
                       CASE WHEN EXISTS(SELECT 1 FROM sijarta.customer c WHERE c.Id = u.Id) THEN 'user'
                            WHEN EXISTS(SELECT 1 FROM sijarta.worker w WHERE w.Id = u.Id) THEN 'worker'
                            ELSE NULL END as role
                FROM sijarta.users u
                WHERE u.PhoneNum = %s AND u.Pwd = %s
                LIMIT 1;
            """, (username, password))
            user = cursor.fetchone()
            return user  # (id, role) or None
    finally:
        conn.close()
    return None

def get_service_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, categoryname
        FROM sijarta.service_category
    """)
    categories = cursor.fetchall()
    conn.close()
    return categories




# Function to retrieve subcategories for a given category ID
def get_service_subcategories(category_id):
    conn = get_db_connection()  # Assuming this function is defined to get the DB connection
    cursor = conn.cursor()
    
    # SQL query to get the subcategories for the specified category ID
    cursor.execute("""
        SELECT id, subcategoryname, description 
        FROM sijarta.service_subcategory
        WHERE servicecategoryid = %s;
    """, [category_id])
    
    subcategories = cursor.fetchall()
    conn.close()
    
    # Structure the subcategories data
    subcategories_list = []
    for subcategory in subcategories:
        subcategories_list.append({
            'id': subcategory[0],
            'subcategoryname': subcategory[1],
            'description': subcategory[2]
        })
    
    return subcategories_list
def get_service_sessions_by_subcategory(subcategory_name):
    """
    This utility function retrieves service sessions for a specific subcategory from the database.
    
    Parameters:
    - subcategory_name (str): The name of the subcategory to filter by.
    
    Returns:
    - dict: A dictionary with subcategory IDs as keys and lists of sessions as values.
    """
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query to get the sessions and their corresponding subcategory IDs
    cursor.execute("""
        SELECT s.subcategoryid, s.session, s.price, sc.subcategoryname
        FROM sijarta.service_session s
        JOIN sijarta.service_subcategory sc ON s.subcategoryid = sc.id
        WHERE sc.subcategoryname = %s
        ORDER BY s.subcategoryid, s.session;
    """, [subcategory_name])  # Pass subcategory_name as a parameter to the query

    # Fetch all results
    rows = cursor.fetchall()
    conn.close()

    # Group the sessions by subcategoryid
    grouped_sessions = {}
    
    for row in rows:
        subcategoryid = row[0]
        session = row[1]
        price = row[2]
        subcategoryname = row[3]
        
        if subcategoryid not in grouped_sessions:
            grouped_sessions[subcategoryid] = {
                'subcategoryname': subcategoryname,
                'sessions': []
            }
        
        grouped_sessions[subcategoryid]['sessions'].append({
            'session': session,
            'price': price
        })

    return grouped_sessions
def get_testimonials_query(subcategory_name):
    query = """
    SELECT DISTINCT
        c.name AS customer_name,
        t.text AS review,
        t.rating,
        s.servicedate,
        w.name AS worker_name
    FROM 
        sijarta.tr_service_order s
    JOIN 
        sijarta.users c ON s.customerid = c.id
    JOIN 
        sijarta.users w ON s.workerid = w.id
    JOIN 
        sijarta.testimoni t ON s.id = t.servicetrid
    JOIN 
        sijarta.service_subcategory sc ON s.subcategoryid = sc.id
    WHERE 
        sc.subcategoryname = %s
    ORDER BY 
        s.servicedate DESC;
    """
    return query

