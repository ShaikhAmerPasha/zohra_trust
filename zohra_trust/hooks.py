app_name = "zohra_trust"
app_title = "Zohra Trust"
app_publisher = "Ameer"
app_description = "Zohra Trust ERPNext: hostel books, stock, students, attendance, results"
app_email = "ameer@example.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "zohra_trust",
# 		"logo": "/assets/zohra_trust/logo.png",
# 		"title": "Zohra Orphanage",
# 		"route": "/zohra_trust",
# 		"has_permission": "zohra_trust.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/zohra_trust/css/zohra_trust.css"
# app_include_js = "/assets/zohra_trust/js/zohra_trust.js"

# include js, css files in header of web template
# web_include_css = "/assets/zohra_trust/css/zohra_trust.css"
# web_include_js = "/assets/zohra_trust/js/zohra_trust.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "zohra_trust/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "zohra_trust/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "zohra_trust.utils.jinja_methods",
# 	"filters": "zohra_trust.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "zohra_trust.install.before_install"
# after_install = "zohra_trust.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "zohra_trust.uninstall.before_uninstall"
# after_uninstall = "zohra_trust.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "zohra_trust.utils.before_app_install"
# after_app_install = "zohra_trust.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "zohra_trust.utils.before_app_uninstall"
# after_app_uninstall = "zohra_trust.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "zohra_trust.build.after_build"

# To hook into the build process of other apps
# The list of apps being built is passed as an argument

# after_app_build = "zohra_trust.build.after_app_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "zohra_trust.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["zohra_trust.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"zohra_trust.tasks.all"
# 	],
# 	"daily": [
# 		"zohra_trust.tasks.daily"
# 	],
# 	"hourly": [
# 		"zohra_trust.tasks.hourly"
# 	],
# 	"weekly": [
# 		"zohra_trust.tasks.weekly"
# 	],
# 	"monthly": [
# 		"zohra_trust.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "zohra_trust.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "zohra_trust.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "zohra_trust.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["zohra_trust.utils.before_request"]
# after_request = ["zohra_trust.utils.after_request"]

# Job Events
# ----------
# before_job = ["zohra_trust.utils.before_job"]
# after_job = ["zohra_trust.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"zohra_trust.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


fixtures = [
	{"dt": "Role", "filters": [["name", "in", ["Data Entry", "Store", "Principal"]]]},
	{"dt": "Custom Field", "filters": [["module", "=", "Trust Operations"]]},
	{"dt": "Custom DocPerm", "filters": [["name", "like", "zt-%"]]},
]

_correction = {"before_cancel": "zohra_trust.utils.correction.check_correction_window"}
doc_events = {
	"Journal Entry": {
		"before_cancel": [
			"zohra_trust.utils.correction.check_correction_window",
			"zohra_trust.utils.voucher.block_direct_journal_cancel",
		]
	},
	**{
		dt: _correction
		for dt in (
			"Boarding Attendance",
			"Material Consumption",
			"Cash Bank Voucher",
			"Food Expenditure Statement",
			"Result Sheet of Inmates",
			"Purchase Invoice",
			"Stock Entry",
		)
	},
}

after_migrate = ["zohra_trust.setup.schema.add_missing_custom_field_columns"]
