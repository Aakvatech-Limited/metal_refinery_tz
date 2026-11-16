frappe.ui.form.on("Refining Batch", {
    refresh(frm) {
        if (frm.doc.docstatus !== 1) return;
        const outputs = (frm.doc.outputs || []).filter(
            row => row.output_lot && ["Closing WIP", "Recoverable Residue", "Finished Metal"].includes(row.output_type)
        );
        if (!outputs.length) return;

        frm.add_custom_button(__("Assay Refining Output"), () => {
            const options = outputs.map(row => row.output_lot);
            frappe.prompt({
                fieldname: "lot",
                fieldtype: "Select",
                label: __("Output Lot"),
                options,
                reqd: 1,
            }, ({ lot }) => {
                frappe.new_doc("Metal Assay", {
                    company: frm.doc.company,
                    metal_lot: lot,
                    uom: frm.doc.weight_uom,
                });
            }, __("Create Output Assay"));
        }, __("Refining Rounds"));

        frm.add_custom_button(__("Create Next Round"), () => {
            const metalTypes = [...new Set(outputs.map(row => row.metal_type))];
            frappe.prompt({
                fieldname: "metal_type",
                fieldtype: "Select",
                label: __("Metal to Refine"),
                options: metalTypes,
                reqd: 1,
            }, ({ metal_type }) => {
                const lot_names = outputs.filter(row => row.metal_type === metal_type)
                    .map(row => row.output_lot);
                frappe.call({
                    method: "metal_refinery_tz.metal_refinery_tz.services.refining_rounds.create_next_round",
                    args: { source_batch: frm.doc.name, lot_names },
                    freeze: true,
                    callback(r) {
                        if (r.message) frappe.set_route("Form", "Refining Batch", r.message);
                    },
                });
            }, __("Create Next Refining Round"));
        }, __("Refining Rounds"));
    },
});
