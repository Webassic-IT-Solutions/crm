import frappe
from frappe.model.document import Document

class CRMNotification(Document):
    def after_insert(self):
        # Send real-time notification to the target user only
        frappe.publish_realtime(
            event="crm_notification",
            message={
                "from_user": self.from_user,
                "to_user": self.to_user,
                "notification_text": self.notification_text,
                "creation": str(self.creation),
                # ✅ ✅ ✅ Send only ONE routing key: force it
                "route_name": "Tasks",
                "hash": self.reference_name if self.reference_name else None
            },
            user=self.to_user
        )

@frappe.whitelist()
def notify_user(args):
    """
    Create and send a CRM Notification.
    """
    args = frappe._dict(args)

    
    if args.owner == args.assigned_to:
        return

    
    if frappe.db.exists("CRM Notification", {
        "to_user": args.assigned_to,
        "reference_doctype": args.redirect_to_doctype,
        "reference_name": args.redirect_to_docname,
        "type": args.notification_type 
    }):
        return

    values = frappe._dict(
        doctype="CRM Notification",
        from_user=args.owner, 
        to_user=args.assigned_to, 
        type=args.notification_type,
        message=args.message,
        notification_text=args.notification_text,
        notification_type_doctype=args.reference_doctype,
        notification_type_doc=args.reference_docname,
        reference_doctype=args.redirect_to_doctype,
        reference_name=args.redirect_to_docname,
    )

    frappe.get_doc(values).insert(ignore_permissions=True)