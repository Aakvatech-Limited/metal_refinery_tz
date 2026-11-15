frappe.query_reports["Refining Yield and Variance"] = {
  filters: [
    {fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company"},
    {fieldname: "from_date", label: __("From Date"), fieldtype: "Date"},
    {fieldname: "to_date", label: __("To Date"), fieldtype: "Date"},
    {fieldname: "metal_type", label: __("Metal"), fieldtype: "Link", options: "Metal Type"},
    {fieldname: "ownership", label: __("Ownership"), fieldtype: "Select", options: "\nCompany Owned\nCustomer Owned"}
  ]
};
