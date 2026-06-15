frappe.pages['agri-gpt'].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({ parent: wrapper, title: 'AgriGPT', single_column: true });
  $(page.body).html(`<div class="agri-gpt"><div id="agri-history" style="min-height:300px;border:1px solid #ddd;padding:12px;margin-bottom:12px"></div><textarea id="agri-question" class="form-control" placeholder="Ask an agricultural question"></textarea><button class="btn btn-primary" id="agri-send" style="margin-top:8px">Send</button></div>`);
  $(page.body).find('#agri-send').on('click', () => {
    const question = $(page.body).find('#agri-question').val();
    frappe.call({method:'farm_management.agri_ai.api.get_agri_response', args:{question}, callback(r){ $('#agri-history').append(`<p><b>You:</b> ${frappe.utils.escape_html(question)}</p><p><b>AgriGPT:</b> ${frappe.utils.escape_html(r.message.response)}</p>`); }});
  });
};
