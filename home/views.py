from django.views.generic import *
from django.http import JsonResponse
from .forms import ContractForm
from .models import *

from admin_panel.models import ActivityLog


class HomeView(TemplateView):
    template_name = 'home/index.html'

    def dispatch(self, request, *args, **kwargs):
        # هر بار کسی صفحه اصلی رو ببینه، یک بازدید اضافه می‌کنیم
        SiteStat.increase_views()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contract_form'] = ContractForm()
        return context




class ContractCreateView(View):
    def post(self, request, *args, **kwargs):
        form = ContractForm(request.POST)
        if form.is_valid():
            contract = form.save()  # 🔹 همین کافیه، سیگنال لاگ رو می‌سازه

            return JsonResponse({
                "ok": True,
                "message": "درخواست شما با موفقیت ثبت شد.",
                "id": contract.id,
            })

        return JsonResponse({
            "ok": False,
            "errors": form.errors,
        }, status=400)



