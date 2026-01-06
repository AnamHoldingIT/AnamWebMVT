from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings

import ghasedak_sms

from .models import ReCode, Referrer
from .forms import ReCodeForm


class ReCodeView(CreateView):
    template_name = "zlink/zlink.html"
    model = ReCode
    form_class = ReCodeForm
    success_url = reverse_lazy("zlink:recode")

    def dispatch(self, request, *args, **kwargs):
        ref = (kwargs.get("ref") or request.GET.get("ref") or "").strip()

        if ref:
            request.session["recode_ref"] = ref

        return super().dispatch(request, *args, **kwargs)

    def is_ajax(self):
        return self.request.headers.get("x-requested-with") == "XMLHttpRequest"

    def form_valid(self, form):
        obj = form.save(commit=False)

        # ✅ one-time: بعد از ثبت، ref از session حذف میشه تا روی درخواست بعدی اثر نذاره
        ref_code = (self.request.session.pop("recode_ref", None) or "").strip()

        if ref_code:
            obj.referrer = Referrer.objects.filter(code=ref_code, is_active=True).first()
        else:
            obj.referrer = None  # ✅ وقتی خالیه برای هیچکس ثبت نشه

        obj.save()
        self.object = obj

        # ===== SMS =====
        phone = obj.phone
        first_name = obj.first_name

        sms_sent = False
        sms_error = None

        try:
            sms_api = ghasedak_sms.Ghasedak(settings.GHASEDAK_API_KEY)

            message = (
                f"{first_name} عزیز،\n"
                "ثبت درخواست شما با موفقیت انجام شد.\n"
                "کارشناسان ما در اسرع وقت با شما در ارتباط خواهند بود."
            )

            line_number = getattr(settings, "GHASEDAK_LINE_NUMBER", "") or "30005006008562"

            response = sms_api.send_single_sms(
                ghasedak_sms.SendSingleSmsInput(
                    message=message,
                    receptor=phone,
                    line_number=str(line_number),
                )
            )

            print("✅ SMS API RESPONSE:", response)
            sms_sent = True

        except ghasedak_sms.error.ApiException as e:
            sms_error = str(e)
            print("❌ SMS ApiException:", sms_error)

        except Exception as e:
            sms_error = str(e)
            print("❌ SMS Unexpected Exception:", sms_error)

        # ===== AJAX =====
        if self.is_ajax():
            payload = {
                "ok": True,
                "message": "درخواستت ثبت شد. تیم آنام به‌زودی با تو تماس می‌گیرد.",
                "sms_sent": sms_sent,
            }
            if sms_error:
                payload["sms_error"] = sms_error
            return JsonResponse(payload, status=200)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if self.is_ajax():
            errors = {field: [str(e) for e in error_list] for field, error_list in form.errors.items()}
            return JsonResponse(
                {"ok": False, "message": "لطفاً اطلاعات خود را درست وارد کنید", "errors": errors},
                status=400,
            )

        return super().form_invalid(form)
