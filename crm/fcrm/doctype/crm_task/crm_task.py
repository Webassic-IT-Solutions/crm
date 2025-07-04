import frappe
from frappe import _
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as assign, remove as unassign
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user
 
#main
class CRMTask(Document):
    def after_insert(self):
        self.assign_to()

    def before_save(self):
        # Check if update is not by owner, always notify
        if not self.is_new():
            # Don't notify if owner is editing their own task
            if self.owner and frappe.session.user != self.owner:
                self.notify_owner_on_update()

            # If assigned_to changed, handle reassignment
            before = self.get_doc_before_save()
            if before and before.assigned_to != self.assigned_to:
                self.unassign_from_previous_user(before.assigned_to)
                self.assign_to()

    def unassign_from_previous_user(self, user):
        unassign(self.doctype, self.name, user)

    def assign_to(self):
        if self.assigned_to:
            assign({
                "assign_to": [self.assigned_to],
                "doctype": self.doctype,
                "name": self.name,
                "description": self.title or self.description,
            })

            notify_user({
                "owner": self.owner,
                "assigned_to": self.assigned_to,
                "notification_type": "Task",
                "message": f"You have been assigned to {self.name}",
                "notification_text": f"{self.owner} assigned you a new task: {self.title}",
                "reference_doctype": self.doctype,
                "reference_docname": self.name,
                "redirect_to_doctype": self.doctype,
                "redirect_to_docname": self.name,
            })

    def notify_owner_on_update(self):
        frappe.logger().info(f"📣 Notifying owner {self.owner} about update by {frappe.session.user}")

        notify_user({
            "owner": frappe.session.user,
            "assigned_to": self.owner,
            "notification_type": "Task",
            "message": f"Task {self.name} has been updated",
            "notification_text": f"Task '{self.title}' has been updated by {frappe.session.user}.",
            "reference_doctype": self.doctype,
            "reference_docname": self.name,
            "redirect_to_doctype": self.doctype,
            "redirect_to_docname": self.name,
            "allow_duplicates": True
        })

    @staticmethod
    def default_list_data():
        columns = [
            {"label": 'Title', "type": 'Data', "key": 'title', "width": '16rem'},
            {"label": 'Status', "type": 'Select', "key": 'status', "width": '8rem'},
            {"label": 'Priority', "type": 'Select', "key": 'priority', "width": '8rem'},
            {"label": 'Due Date', "type": 'Date', "key": 'due_date', "width": '8rem'},
            {"label": 'Assigned To', "type": 'Link', "key": 'assigned_to', "width": '10rem'},
            {"label": 'Last Modified', "type": 'Datetime', "key": 'modified', "width": '8rem'},
        ]

        rows = [
            "name", "title", "description", "assigned_to",
            "due_date", "status", "priority",
            "reference_doctype", "reference_docname", "modified",
        ]

        return {'columns': columns, 'rows': rows}

    @staticmethod
    def default_kanban_settings():
        return {
            "column_field": "status",
            "title_field": "title",
            "kanban_fields": '["description", "priority", "creation"]'
        }
