from django.views.generic import *
from django.http import JsonResponse
from portfolio.models import PortfolioProject
from .forms import ContractForm
from .models import *
from .utils import increase_views_cached
from admin_panel.models import ActivityLog


class HomeView(TemplateView):
    template_name = 'home/index.html'

    def dispatch(self, request, *args, **kwargs):
        increase_views_cached()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contract_form'] = ContractForm()

        # 🔹 پروژه‌های ویژه برای صفحه اصلی (مثلا 3 تا اول)
        context['featured_projects'] = (
            PortfolioProject.active
            .filter(is_featured_home=True)
            .select_related('category')
            .order_by('home_order', '-created_at')[:3]
        )
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



