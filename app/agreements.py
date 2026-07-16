from fastapi import APIRouter
from .db import get_connection
from .remainder import create_reminder_email, send_email
from fastapi import HTTPException
from psycopg.errors import UniqueViolation
from typing import Optional
from pydantic import BaseModel
from datetime import date, timedelta
from .auth import verify_token
from datetime import timedelta
from fastapi import Depends
from fastapi.responses import FileResponse
import pandas as pd
import os

RECEIVER_EMAIL= os.getenv("RECEIVER_EMAIL")

router = APIRouter()
@router.get("/")
def home():
    return {"message": "API is running"}

@router.get("/test-db")
def test_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT NOW();")
    result = cur.fetchone()

    cur.close()
    conn.close()

    return {"time": result}

@router.post("/agreements")
def add_agreement(data: dict,user = Depends(verify_token)):

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO agreements
            (
                emp_id,
                building_name,
                token_no,
                agent_name,
                total_pay,
                received,
                owner_name,
                owner_contact,
                tenant_name,
                tenant_no,
                status,
                renewal_date,
                remarks
            )
            VALUES
            (
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s
            )
            """,
            (
                user["emp_id"],
                data["building_name"],
                data["token_no"],
                data["agent_name"],
                data["total_pay"],
                data["received"],
                data["owner_name"],
                data["owner_contact"],
                data["tenant_name"],
                data["tenant_no"],
                data["status"],
                data["renewal_date"],
                data["remarks"]
            )
        )

        conn.commit()

        cur.close()
        conn.close()
        add_activity( user["emp_id"], "ADD", f"Added agreement for '{data['building_name']}'")

        return {
            "success": True,
            "message": "Agreement Added Successfully"
        }
    except UniqueViolation:

        conn.rollback()

        raise HTTPException(
            status_code=400,
            detail="Token Number already exists"
        )

    finally:

        cur.close()
        conn.close()


@router.get("/display_agreements")
def get_agreements(user = Depends(verify_token)):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            sr_no,
            building_name,
            token_no,
            agent_name,
            status,
            total_pay,
            renewal_date
        FROM agreements
        ORDER BY sr_no DESC
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    agreements = []

    for row in rows:
        agreements.append({
            "sr_no": row[0],
            "building_name": row[1],
            "token_no": row[2],
            "agent_name": row[3],
            "status": row[4],
            "total_pay": float(row[5]) if row[5] else 0,
            "renewal_date": str(row[6]) if row[6] else None
        })

    return agreements


@router.get("/agreements/{agreement_id}")
def get_agreement(agreement_id: int, user = Depends(verify_token)):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
             sr_no,
        emp_id,
        building_name,
        token_no,
        agent_name,
        total_pay,
        received,
        owner_name,
        owner_contact,
        tenant_name,
        tenant_no,
        status,
        renewal_date,
        remarks,
        created_on
        FROM agreements
        WHERE sr_no = %s
    """, (agreement_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return {"message": "Agreement not found"}
    remaining = float(row[5] or 0) - float(row[6] or 0)
    return {
        "sr_no": row[0],
    "emp_id": row[1],
    "building_name": row[2],
    "token_no": row[3],
    "agent_name": row[4],
    "total_pay": float(row[5]) if row[5] else 0,
    "received": float(row[6]) if row[6] else 0,
    "remaining": remaining,
    "owner_name": row[7],
    "owner_contact": row[8],
    "tenant_name": row[9],
    "tenant_no": row[10],
    "status": row[11],
    "renewal_date": str(row[12]) if row[12] else "",
    "remarks": row[13],
    "created_on": str(row[14])
    }


from pydantic import BaseModel

class DeleteRequest(BaseModel):
    emp_id: str

@router.delete("/agreements/{agreement_id}")
def delete_agreement(
    agreement_id: int,
    data: DeleteRequest,user = Depends(verify_token)
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
    """
    SELECT building_name
    FROM agreements
    WHERE sr_no=%s
    """,
    (agreement_id,)
    )

    agreement = cur.fetchone()

    cur.execute(
        "DELETE FROM agreements WHERE sr_no = %s",
        (agreement_id,)
    )

    conn.commit()

    cur.close()
    conn.close()
    add_activity( data.emp_id, "DELETE", f"Deleted agreement for {agreement[0]}", agreement_id)

    return {
        "message": "Agreement deleted successfully"
    }

class Agreement(BaseModel):

    emp_id: Optional[str] = None
    building_name: str
    token_no: str
    agent_name: str

    total_pay: float
    received: float

    owner_name:str
    owner_contact: str
    tenant_name:str
    tenant_no: str

    status: str

    renewal_date: str
    remarks: Optional[str] = None

@router.put("/agreements/{agreement_id}")
def update_agreement(
    agreement_id: int,
    data: Agreement,user = Depends(verify_token)
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE agreements
        SET
            building_name = %s,
            token_no = %s,
            agent_name = %s,
            total_pay = %s,
            received = %s,
            owner_name = %s,
            owner_contact = %s,
            tenant_name = %s,
            tenant_no = %s,
            status = %s,
            renewal_date = %s,
            remarks = %s,
            updated_on = CURRENT_TIMESTAMP
        WHERE sr_no = %s
        """,
        (
            data.building_name,
            data.token_no,
            data.agent_name,
            data.total_pay,
            data.received,
            data.owner_name,
            data.owner_contact,
            data.tenant_name,
            data.tenant_no,
            data.status,
            data.renewal_date,
            data.remarks,
            agreement_id
        )
    )

    conn.commit()

    cur.close()
    conn.close()
    add_activity(user["emp_id"], "EDIT", f"Updated agreement for {data.building_name}", agreement_id)
    return {
        "message": "Agreement updated successfully"
    }


@router.get("/dashboard_stats")
def dashboard_stats(user = Depends(verify_token)):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM agreements"
    )
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM agreements WHERE status='Pending'"
    )
    pending = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM agreements WHERE status='Registered'"
    )
    registered = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM agreements WHERE status='Cancel'"
    )
    cancelled = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM agreements
        WHERE renewal_date >= CURRENT_DATE
        """
    )
    renewals = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "total": total,
        "pending": pending,
        "registered": registered,
        "cancelled": cancelled,
        "renewals": renewals
    }


@router.get("/search_agreements")
def search_agreements(q: str):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM agreements
        WHERE
            building_name ILIKE %s
            OR token_no ILIKE %s
            OR agent_name ILIKE %s
            OR owner_contact ILIKE %s
            OR status ILIKE %s
        ORDER BY sr_no DESC
        """,
        (
            f"%{q}%",
            f"%{q}%",
            f"%{q}%",
            f"%{q}%",
            f"%{q}%"
        )
    )

    rows = cur.fetchall()

    data = []

    for row in rows:
        data.append({
            "sr_no": row[0],
            "building_name": row[2],
            "token_no": row[3],
            "agent_name": row[4],
            "status": row[9]
        })

    cur.close()
    conn.close()

    return data

@router.get("/upcoming_renewals")
def upcoming_renewals():

    conn = get_connection()
    cur = conn.cursor()

    today = date.today()
    next_30_days = today + timedelta(days=30)

    cur.execute("""
        SELECT
            sr_no,
            building_name,
            renewal_date,
            status
        FROM agreements
        WHERE renewal_date
        BETWEEN %s AND %s
        ORDER BY renewal_date ASC
    """, (today, next_30_days))

    rows = cur.fetchall()

    result = []

    for row in rows:
        result.append({
            "sr_no": row[0],
            "building_name": row[1],
            "renewal_date": str(row[2]),
            "status": row[3]
        })
    cur.close()
    conn.close()
    return result


def add_activity(
    emp_id,
    activity_type,
    description,
    agreement_id=None
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO activity_logs
        (
            emp_id,
            activity_type,
            description,
            agreement_id
        )
        VALUES (%s,%s,%s,%s)
    """,
    (
        emp_id,
        activity_type,
        description,
        agreement_id
    ))

    conn.commit()

    cur.close()
    conn.close()


@router.get("/recent_activities")
def recent_activities():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.emp_id,
            u.name,
            a.activity_type,
            a.description,
            a.created_on
        FROM activity_logs a
        LEFT JOIN users u
            ON a.emp_id = u.emp_id
        ORDER BY a.created_on DESC
        LIMIT 5
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "emp_id": row[0],
            "name": row[1],
            "activity_type": row[2],
            "description": row[3],
            "created_on": row[4]
        }
        for row in rows
    ]






def check_agreement_reminders():
    conn= get_connection()
    today = date.today()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            sr_no,
            building_name,
            renewal_date,
            reminder_status
        FROM agreements
        WHERE renewal_date IS NOT NULL
    """)

    agreements = cursor.fetchall()

    for agreement in agreements:

        sr_no = agreement[0]
        building_name = agreement[1]
        renewal_date = agreement[2]
        reminder_status = agreement[3]

        days_left = (renewal_date - today).days
        print(f"Building: {building_name}")
        print(f"Renewal Date: {renewal_date}")
        print(f"Days Left: {days_left}")
        print(f"Reminder Status: {reminder_status}")
        # 15 Days Reminder
        if days_left == 15 and reminder_status < 1:

            send_email(
                RECEIVER_EMAIL,
                "Agreement Renewal Reminder - 15 Days Left",
                create_reminder_email(
                    building_name,
                    renewal_date,
                    15
                )
            )

            cursor.execute("""
                UPDATE agreements
                SET reminder_status = 1
                WHERE sr_no = %s
            """, (sr_no,))

        # 7 Days Reminder
        elif days_left == 7 and reminder_status < 2:

            send_email(
                RECEIVER_EMAIL,
                "Agreement Renewal Reminder - 7 Days Left",
                create_reminder_email(
                    building_name,
                    renewal_date,
                    7
                )
            )

            cursor.execute("""
                UPDATE agreements
                SET reminder_status = 2
                WHERE sr_no = %s
            """, (sr_no,))

        # 1 Day Reminder
        elif days_left == 1 and reminder_status < 3:

            send_email(
                RECEIVER_EMAIL,
                "Final Agreement Renewal Reminder",
                create_reminder_email(
                    building_name,
                    renewal_date,
                    1
                )
            )

            cursor.execute("""
                UPDATE agreements
                SET reminder_status = 3
                WHERE sr_no = %s
            """, (sr_no,))

        # Expired
        elif days_left < 0 and reminder_status < 4:

            send_email(
                RECEIVER_EMAIL,
                "Agreement Expired",
                create_reminder_email(
                    building_name,
                    renewal_date,
                    0
                )
            )

            cursor.execute("""
                UPDATE agreements
                SET reminder_status = 4
                WHERE sr_no = %s
            """, (sr_no,))

    conn.commit()
    cursor.close()

    conn.close()



@router.post("/send_reminders")
def send_reminders():
    check_agreement_reminders()
    return {"message": "Reminders processed"}



@router.get("/my_activities/{emp_id}")
def my_activities(emp_id:str,   
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            activity_type,
            description,
            created_on
        FROM activity_logs
        WHERE emp_id=%s
        ORDER BY created_on DESC
    """,(emp_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "type":row[0],
            "description":row[1],
            "created_on":row[2]
        }
        for row in rows
    ]

@router.get("/export_agreements")
def export_agreements():

    conn = get_connection()

    query = """
    SELECT *
    FROM agreements
    """

    df = pd.read_sql(query, conn)

    file_path = "agreements.xlsx"

    df.to_excel(
        file_path,
        index=False
    )

    conn.close()

    return FileResponse(
        file_path,
        filename="agreements.xlsx"
    )

@router.get("/health")
async def health():
    return {"status": "ok"}