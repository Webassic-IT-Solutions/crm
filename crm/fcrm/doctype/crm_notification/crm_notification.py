import frappe
from frappe.model.document import Document



class CRMNotification(Document):
	def after_insert(self):
		# Send real-time notification to the target user only
		print(F"Send notification {frappe.as_json(self)}")
		notification_dto = {
                "creation": self.creation,
                "from_user": {
                    "name": self.from_user,
                    "full_name": frappe.get_value(
                        "User", self.from_user, "full_name"
                    ),
                },
                "type": self.type,
                "to_user": self.to_user,
                "read": self.read,
                #"hash": get_hash(notification),
                "notification_text": self.notification_text,
                "notification_type_doctype": self.notification_type_doctype,
                "notification_type_doc": self.notification_type_doc,
                "reference_doctype": self.reference_doctype[4:].lower(),
                "reference_name": self.reference_name,
                "route_name": self.reference_doctype[4:].title(),
            }
		frappe.publish_realtime(
			event="crm_notification",
			message=notification_dto,
			user=self.to_user
		)


def notify_user(args):
	"""
	Create and send a CRM Notification to the assigned user, if different from the owner.
	"""
	args = frappe._dict(args)

	if args.owner == args.assigned_to:
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

	# Avoid duplicates
	if frappe.db.exists("CRM Notification", values):
		return

	frappe.get_doc(values).insert(ignore_permissions=True)