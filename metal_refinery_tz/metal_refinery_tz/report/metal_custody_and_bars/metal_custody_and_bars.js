frappe.query_reports["Metal Custody and Bars"] = {
  filters: [
    {fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company"},
    {fieldname: "warehouse", label: __("Warehouse"), fieldtype: "Link", options: "Warehouse"},
    {fieldname: "metal_type", label: __("Metal"), fieldtype: "Link", options: "Metal Type"},
    {fieldname: "ownership", label: __("Ownership"), fieldtype: "Select", options: "\nCompany Owned\nCustomer Owned"},
    {fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer"}
  ]
};
