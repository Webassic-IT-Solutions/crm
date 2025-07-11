# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as assign, remove as unassign
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


class CRMTask(Document):
	def after_insert(self):
		self.assign_to()

	def validate(self):
		if self.is_new() or not self.assigned_to:
			return

		if self.get_doc_before_save().assigned_to != self.assigned_to:
			self.unassign_from_previous_user(self.get_doc_before_save().assigned_to)
			self.assign_to()

	def on_update(self):
		if self.is_new():
			return
		before_save_doc = self.get_doc_before_save()
		if before_save_doc and ( before_save_doc.status != self.status 
	  		or before_save_doc.due_date != frappe.utils.get_datetime(self.due_date)
			or before_save_doc.description != self.description ):
			notify_task_owner_onupdate(self)


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


	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': 'Title',
				'type': 'Data',
				'key': 'title',
				'width': '16rem',
			},
			{
				'label': 'Status',
				'type': 'Select',
				'key': 'status',
				'width': '8rem',
			},
			{
				'label': 'Priority',
				'type': 'Select',
				'key': 'priority',
				'width': '8rem',
			},
			{
				'label': 'Due Date',
				'type': 'Date',
				'key': 'due_date',
				'width': '8rem',
			},
			{
				'label': 'Assigned To',
				'type': 'Link',
				'key': 'assigned_to',
				'width': '10rem',
			},
			{
				'label': 'Last Modified',
				'type': 'Datetime',
				'key': 'modified',
				'width': '8rem',
			},
		]

		rows = [
			"name",
			"title",
			"description",
			"assigned_to",
			"due_date",
			"status",
			"priority",
			"reference_doctype",
			"reference_docname",
			"modified",
		]
		return {'columns': columns, 'rows': rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "title",
			"kanban_fields": '["description", "priority", "creation"]'
		}


def notify_task_owner_onupdate(doc):
    _doc = doc
    updated_by_name = frappe.get_cached_value("User", frappe.session.user, "full_name")
    notification_text = f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{ updated_by_name }</span>
                <span>{ _('has updated task {0} ').format(
                    f'<span class="font-medium text-ink-gray-9">{ doc.title }</span>'
                ) }</span>
            </div>
        """

    message = (
        _("{0} {1} has been updated by {2}").format(
            doc.doctype, doc.title, updated_by_name
        )
    )


    notify_user(
        {
            "owner": frappe.session.user,
            "assigned_to": doc.owner if doc.owner != frappe.session.user else doc.assigned_to,
            "notification_type": "Task",
            "message": message,
            "notification_text": notification_text,
            "reference_doctype": doc.doctype,
            "reference_docname": doc.name,
            "redirect_to_doctype": doc.doctype,
            "redirect_to_docname": doc.name,
        }
    )

#logic for reminder for evry 2 minutes it has to reminde

from frappe.utils import now_datetime

def send_overdue_task_reminders():
	overdue_tasks = frappe.db.sql(
		"""
		SELECT assigned_to, COUNT(*) as task_count
		FROM `tabCRM Task`
		WHERE
			due_date < NOW()
			AND status != 'Completed'
			AND assigned_to IS NOT NULL
		GROUP BY assigned_to
		""",
		(),
		as_dict=True,
	)

	for record in overdue_tasks:
		user = record.assigned_to
		owner = "Administrator"
		count = record.task_count

		if count > 0:
			message = f"You have {count} tasks that are overdue."
			notification_text = f"""
				<div class="mb-2 leading-5 text-ink-gray-5">
					<span class="font-medium text-ink-gray-9">Reminder</span>
					<span>: You have <strong>{count}</strong> tasks that are overdue. Please review them.</span>
				</div>
			"""

			notify_user(
				{
      
					"owner": owner,
					"assigned_to": user,
					"notification_type": "Task",
					"message": message,
					"notification_text": notification_text,
					"reference_doctype": "CRM Task",
					"reference_docname": None,
					"redirect_to_doctype": "CRM Task",
					"redirect_to_docname": None,
				}
			)
	frappe.db.commit()
