from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.http import JsonResponse

from .models import ReCode
from .forms import ReCodeForm


class ReCodeView(CreateView):
    template_name = "zlink/zlink.html"
    model = ReCode
    form_class = ReCodeForm
    success_url = reverse_lazy("zlink:recode")  # برای حالت غیر AJAX

    def is_ajax(self):
        return self.request.headers.get("x-requested-with") == "XMLHttpRequest"

    def form_valid(self, form):
        self.object = form.save()

        if self.is_ajax():
            return JsonResponse(
                {
                    "ok": True,
                    "message": "درخواستت ثبت شد. تیم آنام به‌زودی با تو تماس می‌گیرد.",
                },
                status=200,
            )

        return super().form_valid(form)

    def form_invalid(self, form):
        if self.is_ajax():
            errors = {
                field: [str(e) for e in error_list]
                for field, error_list in form.errors.items()
            }
            return JsonResponse(
                {
                    "ok": False,
                    "message": "لطفاً اطلاعات خود را درست وارد کنید",
                    "errors": errors,
                },
                status=400,
            )

        return super().form_invalid(form)
