import frappe
from frappe.model.document import Document



class CRMNotification(Document):
	def on_update(self):
		# Send real-time notification to the target user only
		frappe.publish_realtime(
			event="crm_notification",
			message=self,
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