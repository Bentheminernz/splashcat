import datetime
import json
import qrcode
from typing import Optional
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db import models
from django.forms import inlineformset_factory
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.core.mail import send_mail
from django.utils import timezone
from django.urls import reverse_lazy

from battles.models import Player, Battle
from battles.tasks import user_request_data_export
from splashcat.decorators import github_webhook
from splatnet_assets.models import Weapon
from . import tasks
from .forms import RegisterForm, AccountSettingsForm, ResendVerificationEmailForm, CodeVerificationForm, AuthenticationForm
from .models import User, GitHubLink, ApiKey, ProfileUrl, Follow, Notification, EmailVerification
from groups.models import Group


# Create your views here.
class LoginView(LoginView):
    form_class = AuthenticationForm
    template_name = 'users/login.html'

    def form_valid(self, form):
        user = form.get_user()
        
        if user.multi_factor_auth_enabled:
            self.request.session['2fa_user_id'] = user.id
            send_verification_code(user, 'login')
            return redirect('users:verify_code_view', action='login')
        
        return super().form_valid(form)
    
def get_svg_for_link(url):
    PLATFORM_SVGS = {
        'bsky.app': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Bluesky</title><path d="M12 10.8c-1.087-2.114-4.046-6.053-6.798-7.995C2.566.944 1.561 1.266.902 1.565.139 1.908 0 3.08 0 3.768c0 .69.378 5.65.624 6.479.815 2.736 3.713 3.66 6.383 3.364.136-.02.275-.039.415-.056-.138.022-.276.04-.415.056-3.912.58-7.387 2.005-2.83 7.078 5.013 5.19 6.87-1.113 7.823-4.308.953 3.195 2.05 9.271 7.733 4.308 4.267-4.308 1.172-6.498-2.74-7.078a8.741 8.741 0 0 1-.415-.056c.14.017.279.036.415.056 2.67.297 5.568-.628 6.383-3.364.246-.828.624-5.79.624-6.478 0-.69-.139-1.861-.902-2.206-.659-.298-1.664-.62-4.3 1.24C16.046 4.748 13.087 8.687 12 10.8Z"/></svg>',
        'x.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>X</title><path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/></svg>',
        'facebook.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Facebook</title><path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"/></svg>',
        'instagram.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Instagram</title><path d="M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077"/></svg>',
        'linkedin.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>LinkedIn</title><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>',
        'github.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>GitHub</title><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>',
        'gitlab.': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>GitLab</title><path d="m23.6004 9.5927-.0337-.0862L20.3.9814a.851.851 0 0 0-.3362-.405.8748.8748 0 0 0-.9997.0539.8748.8748 0 0 0-.29.4399l-2.2055 6.748H7.5375l-2.2057-6.748a.8573.8573 0 0 0-.29-.4412.8748.8748 0 0 0-.9997-.0537.8585.8585 0 0 0-.3362.4049L.4332 9.5015l-.0325.0862a6.0657 6.0657 0 0 0 2.0119 7.0105l.0113.0087.03.0213 4.976 3.7264 2.462 1.8633 1.4995 1.1321a1.0085 1.0085 0 0 0 1.2197 0l1.4995-1.1321 2.4619-1.8633 5.006-3.7489.0125-.01a6.0682 6.0682 0 0 0 2.0094-7.003z"/></svg>',
        'youtube.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>YouTube</title><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
        'tiktok.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>TikTok</title><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg>',
        'pinterest.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Pinterest</title><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"/></svg>',
        'reddit.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Reddit</title><path d="M12 0C5.373 0 0 5.373 0 12c0 3.314 1.343 6.314 3.515 8.485l-2.286 2.286C.775 23.225 1.097 24 1.738 24H12c6.627 0 12-5.373 12-12S18.627 0 12 0Zm4.388 3.199c1.104 0 1.999.895 1.999 1.999 0 1.105-.895 2-1.999 2-.946 0-1.739-.657-1.947-1.539v.002c-1.147.162-2.032 1.15-2.032 2.341v.007c1.776.067 3.4.567 4.686 1.363.473-.363 1.064-.58 1.707-.58 1.547 0 2.802 1.254 2.802 2.802 0 1.117-.655 2.081-1.601 2.531-.088 3.256-3.637 5.876-7.997 5.876-4.361 0-7.905-2.617-7.998-5.87-.954-.447-1.614-1.415-1.614-2.538 0-1.548 1.255-2.802 2.803-2.802.645 0 1.239.218 1.712.585 1.275-.79 2.881-1.291 4.64-1.365v-.01c0-1.663 1.263-3.034 2.88-3.207.188-.911.993-1.595 1.959-1.595Zm-8.085 8.376c-.784 0-1.459.78-1.506 1.797-.047 1.016.64 1.429 1.426 1.429.786 0 1.371-.369 1.418-1.385.047-1.017-.553-1.841-1.338-1.841Zm7.406 0c-.786 0-1.385.824-1.338 1.841.047 1.017.634 1.385 1.418 1.385.785 0 1.473-.413 1.426-1.429-.046-1.017-.721-1.797-1.506-1.797Zm-3.703 4.013c-.974 0-1.907.048-2.77.135-.147.015-.241.168-.183.305.483 1.154 1.622 1.964 2.953 1.964 1.33 0 2.47-.81 2.953-1.964.057-.137-.037-.29-.184-.305-.863-.087-1.795-.135-2.769-.135Z"/></svg>',
        'snapchat.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Snapchat</title><path d="M12.206.793c.99 0 4.347.276 5.93 3.821.529 1.193.403 3.219.299 4.847l-.003.06c-.012.18-.022.345-.03.51.075.045.203.09.401.09.3-.016.659-.12 1.033-.301.165-.088.344-.104.464-.104.182 0 .359.029.509.09.45.149.734.479.734.838.015.449-.39.839-1.213 1.168-.089.029-.209.075-.344.119-.45.135-1.139.36-1.333.81-.09.224-.061.524.12.868l.015.015c.06.136 1.526 3.475 4.791 4.014.255.044.435.27.42.509 0 .075-.015.149-.045.225-.24.569-1.273.988-3.146 1.271-.059.091-.12.375-.164.57-.029.179-.074.36-.134.553-.076.271-.27.405-.555.405h-.03c-.135 0-.313-.031-.538-.074-.36-.075-.765-.135-1.273-.135-.3 0-.599.015-.913.074-.6.104-1.123.464-1.723.884-.853.599-1.826 1.288-3.294 1.288-.06 0-.119-.015-.18-.015h-.149c-1.468 0-2.427-.675-3.279-1.288-.599-.42-1.107-.779-1.707-.884-.314-.045-.629-.074-.928-.074-.54 0-.958.089-1.272.149-.211.043-.391.074-.54.074-.374 0-.523-.224-.583-.42-.061-.192-.09-.389-.135-.567-.046-.181-.105-.494-.166-.57-1.918-.222-2.95-.642-3.189-1.226-.031-.063-.052-.15-.055-.225-.015-.243.165-.465.42-.509 3.264-.54 4.73-3.879 4.791-4.02l.016-.029c.18-.345.224-.645.119-.869-.195-.434-.884-.658-1.332-.809-.121-.029-.24-.074-.346-.119-1.107-.435-1.257-.93-1.197-1.273.09-.479.674-.793 1.168-.793.146 0 .27.029.383.074.42.194.789.3 1.104.3.234 0 .384-.06.465-.105l-.046-.569c-.098-1.626-.225-3.651.307-4.837C7.392 1.077 10.739.807 11.727.807l.419-.015h.06z"/></svg>',
        'twitch.tv': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Twitch</title><path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714Z"/></svg>',
        'discord.': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Discord</title><path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z"/></svg>',
        'whatsapp.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>WhatsApp</title><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>',
        'spotify.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Spotify</title><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>',
        'music.apple.com': '<svg role="img" class="w-5 h-5 inline text-white fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><title>Apple Music</title><path d="M23.994 6.124a9.23 9.23 0 00-.24-2.19c-.317-1.31-1.062-2.31-2.18-3.043a5.022 5.022 0 00-1.877-.726 10.496 10.496 0 00-1.564-.15c-.04-.003-.083-.01-.124-.013H5.986c-.152.01-.303.017-.455.026-.747.043-1.49.123-2.193.4-1.336.53-2.3 1.452-2.865 2.78-.192.448-.292.925-.363 1.408-.056.392-.088.785-.1 1.18 0 .032-.007.062-.01.093v12.223c.01.14.017.283.027.424.05.815.154 1.624.497 2.373.65 1.42 1.738 2.353 3.234 2.801.42.127.856.187 1.293.228.555.053 1.11.06 1.667.06h11.03a12.5 12.5 0 001.57-.1c.822-.106 1.596-.35 2.295-.81a5.046 5.046 0 001.88-2.207c.186-.42.293-.87.37-1.324.113-.675.138-1.358.137-2.04-.002-3.8 0-7.595-.003-11.393zm-6.423 3.99v5.712c0 .417-.058.827-.244 1.206-.29.59-.76.962-1.388 1.14-.35.1-.706.157-1.07.173-.95.045-1.773-.6-1.943-1.536a1.88 1.88 0 011.038-2.022c.323-.16.67-.25 1.018-.324.378-.082.758-.153 1.134-.24.274-.063.457-.23.51-.516a.904.904 0 00.02-.193c0-1.815 0-3.63-.002-5.443a.725.725 0 00-.026-.185c-.04-.15-.15-.243-.304-.234-.16.01-.318.035-.475.066-.76.15-1.52.303-2.28.456l-2.325.47-1.374.278c-.016.003-.032.01-.048.013-.277.077-.377.203-.39.49-.002.042 0 .086 0 .13-.002 2.602 0 5.204-.003 7.805 0 .42-.047.836-.215 1.227-.278.64-.77 1.04-1.434 1.233-.35.1-.71.16-1.075.172-.96.036-1.755-.6-1.92-1.544-.14-.812.23-1.685 1.154-2.075.357-.15.73-.232 1.108-.31.287-.06.575-.116.86-.177.383-.083.583-.323.6-.714v-.15c0-2.96 0-5.922.002-8.882 0-.123.013-.25.042-.37.07-.285.273-.448.546-.518.255-.066.515-.112.774-.165.733-.15 1.466-.296 2.2-.444l2.27-.46c.67-.134 1.34-.27 2.01-.403.22-.043.442-.088.663-.106.31-.025.523.17.554.482.008.073.012.148.012.223.002 1.91.002 3.822 0 5.732z"/></svg>'
    }

    for platform, svg_code in PLATFORM_SVGS.items():
        if platform in url:
            return svg_code
    return """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5 inline">
        <path d="M12.232 4.232a2.5 2.5 0 013.536 3.536l-1.225 1.224a.75.75 0 001.061 1.06l1.224-1.224a4 4 0 00-5.656-5.656l-3 3a4 4 0 00.225 5.865.75.75 0 00.977-1.138 2.5 2.5 0 01-.142-3.667l3-3z"></path>
        <path d="M11.603 7.963a.75.75 0 00-.977 1.138 2.5 2.5 0 01.142 3.667l-3 3a2.5 2.5 0 01-3.536-3.536l1.225-1.224a.75.75 0 00-1.061-1.06l-1.224 1.224a4 4 0 105.656 5.656l3-3a4 4 0 00-.225-5.865z"></path>
    </svg>
    """

def profile(request, username: str):
    user = get_object_or_404(User, username__iexact=username)
    latest_battles = user.battles.with_prefetch().order_by('-played_time') \
                         .select_related('vs_stage__name')[:18]
    splashtag = latest_battles[0].splashtag if latest_battles else None

    win_count = user.battles.filter(judgement='WIN').count()
    lose_count = user.battles.filter(judgement__in=['LOSE', 'DEEMED_LOSE']).count()
    win_rate = win_count / (win_count + lose_count) * 100 if win_count + lose_count else 0
    aggregates = Player.objects.filter(team__battle__uploader=user, is_self=True).aggregate(
        average_kills=models.Avg('kills'),
        average_assists=models.Avg('assists'),
        average_deaths=models.Avg('deaths'),
        average_specials=models.Avg('specials'),
        average_paint=models.Avg('paint'),
    )

    period_ago = datetime.datetime.now() - datetime.timedelta(hours=24)
    period_ago_wins = user.battles.filter(judgement='WIN', played_time__gte=period_ago).count()
    period_ago_loses = user.battles.filter(judgement__in=['LOSE', 'DEEMED_LOSE']).filter(played_time__gte=period_ago) \
        .count()
    period_ago_win_rate = period_ago_wins / (period_ago_wins + period_ago_loses) * 100 if \
        period_ago_wins + period_ago_loses else None

    most_used_weapon = Player.objects.filter(team__battle__uploader=user, is_self=True) \
        .values('weapon').annotate(count=models.Count('weapon')).order_by('-count').first()
    most_used_weapon = Weapon.objects.get(pk=most_used_weapon['weapon']) if most_used_weapon else None

    total_uploader_disconnects = Player.objects.filter(team__battle__uploader=user, is_self=True,
                                                       disconnect=True).count()
    
    following_list = Follow.objects.filter(follower=user).select_related('followed').order_by('-followed_on')
    followers_list = Follow.objects.filter(followed=user).select_related('follower').order_by('-followed_on')
    followed_user = user

    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, followed=user).exists()
    else:
        is_following = False

    processed_links = []

    for link in user.profile_urls.all():
        svg_code = get_svg_for_link(link.url)
        processed_links.append({
            'url': link.url,
            'svg': svg_code,
            'is_rel_me_verified': link.is_rel_me_verified,
        })

    context = {
        'profile_user': user,
        'splashtag': splashtag,
        'latest_battles': latest_battles,
        'win_count': win_count,
        'lose_count': lose_count,
        'win_rate': win_rate,
        'period_ago_wins': period_ago_wins,
        'period_ago_loses': period_ago_loses,
        'period_ago_win_rate': period_ago_win_rate,
        'aggregates': aggregates,
        'most_used_weapon': most_used_weapon,
        'total_uploader_disconnects': total_uploader_disconnects,
        'following_list': following_list,
        'followers_list': followers_list,
        'followed_user': followed_user,
        'is_following': is_following,
        'processed_links': processed_links,
    }


    return render(request, 'users/profile.html', context)


def profile_opengraph(request, username: str):
    user = get_object_or_404(User, username__iexact=username)
    latest_battles = user.battles.with_prefetch().order_by('-played_time') \
                         .select_related('vs_stage__name')[:12]
    splashtag = latest_battles[0].splashtag if latest_battles else None

    win_count = user.battles.filter(judgement='WIN').count()
    lose_count = user.battles.filter(judgement__in=['LOSE', 'DEEMED_LOSE']).count()
    win_rate = win_count / (win_count + lose_count) * 100 if win_count + lose_count else 0

    period_ago = datetime.datetime.now() - datetime.timedelta(hours=24)
    period_ago_wins = user.battles.filter(judgement='WIN', played_time__gte=period_ago).count()
    period_ago_loses = user.battles.filter(judgement__in=['LOSE', 'DEEMED_LOSE']).filter(played_time__gte=period_ago) \
        .count()
    period_ago_win_rate = period_ago_wins / (period_ago_wins + period_ago_loses) * 100 if \
        period_ago_wins + period_ago_loses else None

    most_used_weapons = Player.objects.filter(team__battle__uploader=user, is_self=True) \
                            .values('weapon').annotate(count=models.Count('weapon')).order_by('-count')[:3]
    most_used_weapons = Weapon.objects.filter(pk__in=[weapon['weapon'] for weapon in most_used_weapons])

    return render(request, 'users/opengraph/user.html',
                  {
                      'profile_user': user,
                      'splashtag': splashtag,
                      'latest_battles': latest_battles,
                      'win_count': win_count,
                      'lose_count': lose_count,
                      'win_rate': win_rate,
                      'period_ago_win_rate': period_ago_win_rate,
                      'most_used_weapons': most_used_weapons,
                  })


def profile_json(request, username: str):
    user = get_object_or_404(User, username__iexact=username)
    try:
        latest_battle: Optional[Battle] = user.battles.with_prefetch().latest('played_time')
    except Battle.DoesNotExist:
        latest_battle = None
    splashtag = latest_battle.splashtag if latest_battle else None

    win_count = user.battles.filter(judgement='WIN').count()
    lose_count = user.battles.filter(judgement__in=['LOSE', 'DEEMED_LOSE']).count()
    win_rate = win_count / (win_count + lose_count) * 100 if win_count + lose_count else None
    aggregates = Player.objects.filter(team__battle__uploader=user, is_self=True).aggregate(
        average_kills=models.Avg('kills'),
        average_assists=models.Avg('assists'),
        average_deaths=models.Avg('deaths'),
        average_specials=models.Avg('specials'),
        average_paint=models.Avg('paint'),
    )

    period_ago = datetime.datetime.now() - datetime.timedelta(hours=24)
    period_ago_wins = user.battles.filter(judgement='WIN', played_time__gte=period_ago).count()
    period_ago_loses = user.battles.filter(judgement__in=['LOSE', 'DEEMED_LOSE']).filter(played_time__gte=period_ago) \
        .count()
    period_ago_win_rate = period_ago_wins / (period_ago_wins + period_ago_loses) * 100 if \
        period_ago_wins + period_ago_loses else None
    period_ago_aggregates = Player.objects.filter(team__battle__uploader=user, is_self=True,
                                                  team__battle__played_time__gt=period_ago).aggregate(
        average_kills=models.Avg('kills'),
        average_assists=models.Avg('assists'),
        average_deaths=models.Avg('deaths'),
        average_specials=models.Avg('specials'),
        average_paint=models.Avg('paint'),
    )

    try:
        most_used_weapon = Player.objects.filter(team__battle__uploader=user, is_self=True) \
            .values('weapon').annotate(count=models.Count('weapon')).order_by('-count').first()
    except Player.DoesNotExist:
        most_used_weapon = None
    most_used_weapon = Weapon.objects.get(pk=most_used_weapon['weapon']) if most_used_weapon else None

    total_uploader_disconnects = Player.objects.filter(team__battle__uploader=user, is_self=True,
                                                       disconnect=True).count()

    splashtag_badge_images = [(badge.image.url if badge else None) for badge in
                              splashtag['badges']] if splashtag else None

    return JsonResponse({
        'splashtag': {
            'name': splashtag['name'],
            'name_id': splashtag['name_id'],
            'title': latest_battle.player.byname,
            'background_url': splashtag['background'].image.url,
            'badge_urls': splashtag_badge_images,
            'text_color': "#" + splashtag['background'].text_color.to_hex(),
        } if splashtag else None,
        'win_count': win_count,
        'lose_count': lose_count,
        'win_rate': win_rate,
        '24h_wins': period_ago_wins,
        '24h_loses': period_ago_loses,
        '24h_win_rate': period_ago_win_rate,
        'aggregates': aggregates,
        '24h_aggregates': period_ago_aggregates,
        'most_used_weapon': {
            'name': most_used_weapon.name.string,
            'image': most_used_weapon.flat_image.url,
            'image_3d': most_used_weapon.image_3d.url,
            'sub_name': most_used_weapon.sub.name.string,
            'sub_overlay_image': most_used_weapon.sub.overlay_image.url,
            'sub_mask_image': most_used_weapon.sub.mask_image.url,
            'special_name': most_used_weapon.special.name.string,
            'special_overlay_image': most_used_weapon.special.overlay_image.url,
            'special_mask_image': most_used_weapon.special.mask_image.url,
        } if most_used_weapon else None,
        'total_uploader_disconnects': total_uploader_disconnects,
        'profile_picture': user.profile_picture.url,
        'latest_battle_color': f"#{latest_battle.player.team.color.to_hex()}" if latest_battle else None,
        'sponsor_favorite_color': f"#{user.favorite_color.to_hex()}" if user.favorite_color else None,
    })


def profile_battle_list(request, username: str):
    user = get_object_or_404(User, username__iexact=username)
    battles = user.battles.with_prefetch().order_by('-played_time') \
        .select_related('vs_stage__name')

    paginator = Paginator(battles, 24)

    page = request.GET.get('page', 1)
    try:
        page = paginator.page(page)
    except (ValueError, TypeError, EmptyPage, InvalidPage):
        return HttpResponseBadRequest('Invalid page number.')

    return render(request, 'users/profile_battle_list.html', {
        'profile_user': user,
        'page': page,
        'splashtag': user.get_splashtag,
    })


def profile_album(request, username: str):
    user = get_object_or_404(User, username__iexact=username)

    return render(request, 'users/profile_album.html', {
        'profile_user': user,
        'splashtag': user.get_splashtag,
    })


def profile_qr_code(request, username: str):
    user = get_object_or_404(User, username__iexact=username)
    if not user.coral_friend_url:
        return HttpResponseBadRequest('User does not have coral friend url.')
    qr_code = qrcode.make(f"{user.coral_friend_url}?via=qr&utm_source=splashcat.ink&utm_medium=qr")
    response = HttpResponse(content_type="image/png")
    qr_code.save(response, "PNG")
    return response


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            if settings.HCAPTCHA_SECRET_KEY:
                hcaptcha_token = request.POST.get('h-captcha-response')
                if not hcaptcha_token:
                    messages.error(request, 'hCaptcha verification failed.')
                    return render(request, 'users/register.html', {
                        'form': form,
                    })
                hcaptcha_response = requests.post('https://hcaptcha.com/siteverify', data={
                    'secret': settings.HCAPTCHA_SECRET_KEY,
                    'response': hcaptcha_token,
                }).json()
                if not hcaptcha_response['success']:
                    messages.error(request, 'hCaptcha verification failed.')
                    return render(request, 'users/register.html', {
                        'form': form,
                    })

            user = form.save()

            user.send_verification_email()
            tasks.generate_user_profile_picture.delay(user.pk)

            messages.success(request, 'Your account has been created. Please check your email to verify your account.')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {
        'form': form,
    })


@csrf_exempt
@require_http_methods(['POST'])
@github_webhook
def github_sponsors_webhook(request):
    data = json.loads(request.body)
    action = data['action']

    github_link, _created = GitHubLink.objects.get_or_create(github_id=data['sponsorship']['sponsor']['id'])

    if action == 'created' or action == 'tier_changed':
        github_link.is_sponsor = True
        github_link.is_sponsor_public = data['sponsorship']['privacy_level'] == 'public'
        github_link.sponsorship_amount_usd = data['sponsorship']['tier']['monthly_price_in_dollars']
    elif action == 'edited':
        github_link.is_sponsor_public = data['sponsorship']['privacy_level'] == 'public'
        github_link.sponsorship_amount_usd = data['sponsorship']['tier']['monthly_price_in_dollars']
    elif action == 'cancelled':
        github_link.is_sponsor = False
        github_link.is_sponsor_public = False
        github_link.sponsorship_amount_usd = 0
    github_link.save()
    return HttpResponse("ok")


@login_required
def user_settings(request):
    profile_url_form_set = inlineformset_factory(User, ProfileUrl, fields=["url"], can_delete_extra=False)
    if request.method == 'POST':
        form = AccountSettingsForm(request.POST, request.FILES, instance=request.user)
        formset = profile_url_form_set(request.POST, instance=request.user)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            tasks.validate_rel_me_links.delay(request.user.id)
            return redirect('users:settings')
    else:
        form = AccountSettingsForm(instance=request.user)
        formset = profile_url_form_set(instance=request.user)
    return render(request, 'users/settings.html', {
        'form': form,
        'formset': formset,
    })


@login_required
@require_http_methods(['POST'])
def link_github_account(request):
    if request.POST.get('is_refresh', False) == 'true':
        request.session['github_attempting_refresh'] = True

    return redirect('https://github.com/login/oauth/authorize?'
                    f'client_id={settings.GITHUB_OAUTH_CLIENT_ID}')


@login_required
def link_github_account_callback(request):
    github_session_code = request.GET.get('code')
    if not github_session_code:
        return HttpResponseBadRequest()
    response = requests.post('https://github.com/login/oauth/access_token',
                             data={
                                 'client_id': settings.GITHUB_OAUTH_CLIENT_ID,
                                 'client_secret': settings.GITHUB_OAUTH_CLIENT_SECRET,
                                 'code': github_session_code,
                             },
                             headers={
                                 'Accept': 'application/json',
                             })
    if response.status_code != 200:
        return HttpResponseBadRequest()
    github_access_token = response.json()['access_token']
    response = requests.get('https://api.github.com/user',
                            headers={
                                'Authorization': f'token {github_access_token}',
                            })
    if response.status_code != 200:
        return HttpResponseBadRequest()

    if hasattr(request.user, 'github_link'):
        old_link = request.user.github_link
        old_link.linked_user = None
        old_link.save()

    github_user_id = response.json()['id']
    github_username = response.json()['login']
    GitHubLink.objects.update_or_create(github_id=github_user_id, defaults={
        'linked_user': request.user,
        'github_username': github_username,
    })

    messages.add_message(request, messages.SUCCESS,
                         f'Linked GitHub account @{github_username} to @{request.user.username}!'
                         )

    if request.session.get('github_attempting_refresh'):
        del request.session['github_attempting_refresh']

        graphql_query = """
        query {
          user(login:"%s") {
            sponsorshipForViewerAsSponsorable(activeOnly:true) {
                isOneTimePayment
                privacyLevel
                tier {
                    name
                    monthlyPriceInDollars
              }  
            }
          }
        }""" % github_username

        response = requests.post('https://api.github.com/graphql',
                                 json={'query': graphql_query},
                                 headers={
                                     'Authorization': f'token {settings.GITHUB_PERSONAL_ACCESS_TOKEN}',
                                 })
        if response.status_code == 200:
            data = response.json()['data']['user']['sponsorshipForViewerAsSponsorable']
            github_link = request.user.github_link
            if data:
                tier = data['tier']
                github_link.is_sponsor = data['isOneTimePayment'] is False
                github_link.is_sponsor_public = data['privacyLevel'] == 'PUBLIC'
                github_link.sponsorship_amount_usd = tier['monthlyPriceInDollars']
            else:
                github_link.is_sponsor = False
                github_link.is_sponsor_public = False
                github_link.sponsorship_amount_usd = 0
            github_link.save()

    return redirect('users:settings')


@login_required
@require_http_methods(['POST'])
def create_api_key(request):
    api_key = ApiKey.objects.create(user=request.user, note=request.POST.get('note', ''))
    messages.add_message(request, messages.SUCCESS,
                         f'Created API key `{api_key.key}` for @{request.user.username}!'
                         )
    return redirect('users:settings')


@login_required
@require_http_methods(['POST'])
def delete_api_key(request, key):
    api_key = get_object_or_404(ApiKey, key=key, user=request.user)
    api_key.delete()
    messages.add_message(request, messages.SUCCESS,
                         f'Deleted API key `{key}` for @{request.user.username}!'
                         )
    return redirect('users:settings')


def verify_email(request, user_id, token):
    user = get_object_or_404(User, id=user_id)
    correct_token = default_token_generator.check_token(user, token)
    if not correct_token:
        return HttpResponseBadRequest()
    user.verified_email = True
    user.is_active = True
    user.save()
    messages.add_message(request, messages.SUCCESS,
                         f'Verified email for @{user.username}!'
                         )
    return redirect('home')


def resend_verification_email(request):
    if request.method == 'POST':
        form = ResendVerificationEmailForm(request.POST)
        if form.is_valid():
            form.send_email()
            messages.add_message(request, messages.SUCCESS,
                                 f'Verification email sent to {form.cleaned_data["email"]}!'
                                 )
            return redirect('home')
    else:
        form = ResendVerificationEmailForm()
    return render(request, 'users/resend_verification_email.html', {
        'form': form,
    })


@login_required
@require_http_methods(['POST'])
def request_data_export(request):
    user: User = request.user
    # check that the last data export was more than 24 hours ago
    if (user.last_data_export and user.last_data_export > datetime.datetime.now(
            tz=user.last_data_export.tzinfo) - datetime.timedelta(days=1)):
        messages.add_message(request, messages.ERROR,
                             f'You can only request a data export once per day.'
                             )
        return redirect('users:settings')
    if user.data_export_pending:
        messages.add_message(request, messages.ERROR,
                             f'You already have a data export pending.'
                             )
        return redirect('users:settings')
    user.data_export_pending = True
    user.last_data_export = datetime.datetime.now()
    user_request_data_export.delay(user.pk)
    user.save()
    messages.add_message(request, messages.SUCCESS,
                         f'Requested data export for @{user.username}! You should receive an email soon.'
                         )
    return redirect('users:settings')

def profile_follows(request, username: str, view_type: str):
    user = get_object_or_404(User, username__iexact=username)

    if view_type == 'followers':
        follow_list = Follow.objects.filter(followed=user).select_related('follower').order_by('-followed_on')
    elif view_type == 'following':
        follow_list = Follow.objects.filter(follower=user).select_related('followed').order_by('-followed_on')
    else:
        return redirect('profile', username=user.username)

    if request.user.is_authenticated:
        is_following_list = [
            Follow.objects.filter(follower=request.user, followed=follow.follower if view_type == 'followers' else follow.followed).exists()
            for follow in follow_list
        ]
        is_following = Follow.objects.filter(follower=request.user, followed=user).exists()
    else:
        is_following_list = [False] * follow_list.count()
        is_following = False

    return render(request, 'users/profile_follows.html', {
        'profile_user': user,
        'splashtag': user.get_splashtag,
        'follow_list': zip(follow_list, is_following_list),
        'follow_type': view_type,
        'is_following': is_following
    })


@login_required
def follow_user(request, username):
    followed_user = get_object_or_404(User, username__iexact=username)

    if request.user == followed_user:
        messages.error(request, "You cannot follow yourself.")
    elif Follow.objects.filter(follower=request.user, followed=followed_user).exists():
        messages.error(request, f"You are already following {followed_user.username}.")
    else:
        Follow.objects.create(follower=request.user, followed=followed_user)

        Notification.objects.create(
            recipient=followed_user,
            sender=request.user,
            message=f'followed you.',
            is_read=False
        )

        messages.success(request, f"You are now following {followed_user.username}.")
    
    return redirect(request.META.get('HTTP_REFERER', 'profile'))

@login_required
def unfollow_user(request, username):
    followed_user = get_object_or_404(User, username=username)

    follow_instance = Follow.objects.filter(follower=request.user, followed=followed_user).first()
    if follow_instance:
        follow_instance.delete()
        messages.success(request, f"You have unfollowed {followed_user.username}.")
    else:
        messages.error(request, "You are not following this user.")

    return redirect(request.META.get('HTTP_REFERER', 'profile'))

@login_required
def mark_notifications_as_read(request):
    if request.method == "GET":
        unread_notifications = request.user.notifications.filter(is_read=False)
        unread_notifications.update(is_read=True)

        notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')

        return render(request, 'includes/notification_menu.html', {
            'notifications': notifications
        })
    return JsonResponse({'success': False}, status=400)

@login_required
def get_notifications(request):
    unread_notifications = request.user.notifications.filter(is_read=False).exists()
    notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')
    return render(request, 'includes/notification_menu.html', {
        'notifications': notifications,
        'unread_notifications': unread_notifications
    })

@login_required
def set_user_timezone(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_local_timezone = data.get('user_local_timezone')
        if user_local_timezone:
            user = request.user
            if str(request.user.timezone) != user_local_timezone:
                user.timezone = user_local_timezone
                user.save()
                return JsonResponse({'success': True, 'updated':True})
            else:
                return JsonResponse({'success': True, 'updated':False})
        else:
            return JsonResponse({'success': False})
    
    return JsonResponse({'success': False}, status=400)

def send_verification_code(user, action):
    user.email_verifications.filter(action=action).delete()
    code = EmailVerification.generate_six_digit_code()

    code_instance = EmailVerification.objects.create(
        user=user,
        code=code,
        action=action,
        expires_at=timezone.now() + timedelta(minutes=10)
    )
    action_display = dict(EmailVerification.ACTION_CHOICES).get(action, 'Unknown Action')

    send_mail(
        subject=f'Your {action_display.title()} Verification Code',
        message=f'Hello @{code_instance.user.username}\nYour verification code is {code_instance.code}. This code will expire in 10 minutes.\n\nIf you did not request this code, please reset your password immediately.',
        from_email='Splashcat <grizzco@splashcat.ink>',
        recipient_list=[user.email]
    )

def verify_code_view(request, action):
    form = CodeVerificationForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            code = form.cleaned_data.get('code')
            user_id = request.session.get('2fa_user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    verification_instance = EmailVerification.objects.get(
                        user=user,
                        action=action,
                        code=code,
                        expires_at__gt=timezone.now()
                    )

                    if action == 'login':
                        login(request, user)
                        messages.success(request, 'Login Verification Successful.')
                        request.session.pop('2fa_user_id', None)
                        return redirect('home')
                    
                    elif action == 'account_deletion':
                        user.delete()
                        messages.success(request, 'Account Deleted Successfully.')
                        return redirect('home')
                    
                    elif action == 'disable_email_2fa':
                        user.multi_factor_auth_enabled = False
                        user.save()
                        messages.success(request, 'Email 2fa has been disabled.')
                        return redirect('users:settings')
                    
                    elif action == 'password_change':
                        request.session['password_reset_verified_user_id'] = user.id
                        request.session['2fa_user_id'] = user.id
                        return redirect('users:password_change_form')
                    
                    elif action == 'delete_group':
                        group_id = request.session.get('group_id')
                        group = get_object_or_404(Group, id=group_id)
                        group.delete()
                        messages.success(request, 'Group Deleted Successfully.')
                        return redirect('groups:index')
                    
                    verification_instance.delete()

                except (User.DoesNotExist, EmailVerification.DoesNotExist):
                    messages.error(request, 'Invalid code.')
            else:
                messages.error(request, 'Invalid session or user not found.')
        else:
            messages.error(request, 'Invalid code.')

    action_display = dict(EmailVerification.ACTION_CHOICES).get(action, 'Unknown Action')
    context = {
        'form': form,
        'action_display': action_display
    }

    return render(request, 'users/verify_code.html', context)

@login_required
def request_delete_verification(request):
    user = request.user
    action = 'account_deletion'

    request.session['2fa_user_id'] = user.id

    send_verification_code(user, action)
    messages.info(request, 'A verification code has been sent to your email.')

    return redirect('users:verify_code_view', action='account_deletion')

@login_required
def enable_two_factor_auth_email(request):
    user = request.user
    user.multi_factor_auth_enabled = True
    user.save()

    messages.success(request, 'Email 2fa has been enabled.')
    return redirect('users:settings')

@login_required
def disable_two_factor_auth_email(request):
    user = request.user
    action = 'disable_email_2fa'

    request.session['2fa_user_id'] = user.id

    send_verification_code(user, action)
    messages.info(request, 'A verification code has been sent to your email.')

    return redirect('users:verify_code_view', action='disable_email_2fa')

@login_required
def user_password_reset(request):
    user = request.user
    send_verification_code(user, 'password_change')
    request.session['2fa_user_id'] = user.id
    return redirect('users:verify_code_view', action='password_change')

class UserPasswordChangeView(PasswordChangeView):
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:password_change_done')

    def dispatch(self, request, *args, **kwargs):
        if request.user.multi_factor_auth_enabled:
            if not request.session.get('password_reset_verified_user_id'):
                messages.error(request, 'Unauthorized access to password reset.')
                return redirect('users:password_change')

        # Clear session variable for one-time verification
        request.session.pop('password_reset_verified_user_id', None)
        return super().dispatch(request, *args, **kwargs)
