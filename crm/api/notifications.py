import frappe
from frappe.query_builder import Order
from frappe.query_builder.functions import Count


@frappe.whitelist()
def get_notifications(page_number=1, page_size=20):
    offset  = (page_number - 1) * page_size
    print(offset)
    Notification = frappe.qb.DocType("CRM Notification")

    count_all = Count('1').as_("count")

    query = (
        frappe.qb.from_(Notification)
        .where(Notification.to_user == frappe.session.user)
    )
    notifications = (
        query
        .select("*")
        .orderby("creation", order=Order.desc)
        .limit(page_size)
        .offset(offset)
        ).run(as_dict=True)

    total_count = (
         query
        .select(count_all)
    ).run(as_dict=True) [0]['count']

    unread_count = (
         query
        .select(count_all)
        .where(Notification.read == 0)
    ).run(as_dict=True) [0]['count']

    _notifications = []
    for notification in notifications:
        _notifications.append(
            {
                "creation": notification.creation,
                "from_user": {
                    "name": notification.from_user,
                    "full_name": frappe.get_value(
                        "User", notification.from_user, "full_name"
                    ),
                },
                "type": notification.type,
                "to_user": notification.to_user,
                "read": notification.read,
                "hash": get_hash(notification),
                "notification_text": notification.notification_text,
                "notification_type_doctype": notification.notification_type_doctype,
                "notification_type_doc": notification.notification_type_doc,
                "reference_doctype": notification.reference_doctype[4:].lower(),
                "reference_name": notification.reference_name,
                "route_name": notification.reference_doctype[4:].title(),
            }
        )
    page_rows_count = len(notifications)

    return {"data": _notifications, "page_rows_count": page_rows_count, "total_count": total_count, "unread_count": unread_count }


@frappe.whitelist()
def mark_as_read(user=None, doc=None):
    user = user or frappe.session.user
    filters = {"to_user": user, "read": False}
    or_filters = []
    if doc:
        or_filters = [
            {"comment": doc},
            {"notification_type_doc": doc},
        ]
    for n in frappe.get_all("CRM Notification", filters=filters, or_filters=or_filters):
        d = frappe.get_doc("CRM Notification", n.name)
        d.read = True
        d.save()

def get_hash(notification):
    _hash = ""
    if notification.type == "Mention" and notification.notification_type_doc:
        _hash = "#" + notification.notification_type_doc

    if notification.type == "WhatsApp":
        _hash = "#whatsapp"

    if notification.type == "Assignment" and notification.notification_type_doctype == "CRM Task":
        _hash = "#tasks"
        if "has been removed by" in notification.message:
            _hash = ""
    return _hash