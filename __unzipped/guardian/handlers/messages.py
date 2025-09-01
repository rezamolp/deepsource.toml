from telegram import Update
from telegram.ext import ContextTypes
from services.channel import change_public_link
from utils.validators import normalize_phone
from utils.keyboards import main_menu, otp_keyboard, back_menu
import logging, uuid

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or '').strip()
    logger = logging.getLogger(__name__)
    logger.info('message_received', extra={
        'event': 'message_received',
        'chat_id': getattr(update.effective_chat, 'id', None),
        'user_id': getattr(update.effective_user, 'id', None),
        'state': dict(context.user_data),
        'action': 'route',
    })
    if text in {"بازگشت", "back", "/back"}:
        context.user_data.clear()
        await update.message.reply_text('بازگشت به منوی اصلی.', reply_markup=main_menu()); return
    if context.user_data.get('waiting_for_channel'):
        base = text.split('/')[-1].lstrip('@')
        context.user_data['waiting_for_channel'] = False
        logger.info('channel_set', extra={'event':'channel_set','base_username':base})
        # persist to telemetry channels[]
        try:
            from utils.data import load_data, save_data
            d = load_data() or {}
            channels = d.get('channels', [])
            if base not in channels:
                channels.append(base)
            d['channels'] = channels
            save_data(d)
        except Exception:
            pass
        await update.message.reply_text(f'کانال ثبت شد: @{base}', reply_markup=main_menu()); return
    if context.user_data.get('waiting_for_manual'):
        base = text.split('/')[-1].lstrip('@')
        await change_public_link(0, base)
        context.user_data['waiting_for_manual'] = False
        logger.info('manual_rotation', extra={'event':'manual_rotation','base_username':base})
        await update.message.reply_text(f'لینک تغییر کرد: @{base}', reply_markup=main_menu()); return
    if context.user_data.get('waiting_for_phone'):
        trace_id = str(uuid.uuid4())
        phone = normalize_phone(text)
        if not phone:
            logger.warning('phone_invalid', extra={'event':'phone_invalid','trace_id':trace_id})
            await update.message.reply_text('❌ شماره معتبر نیست. مثال: +989123456789'); return
        context.user_data['waiting_for_phone'] = False
        context.user_data['waiting_for_code'] = True
        context.user_data['phone'] = phone
        context.user_data['trace_id'] = trace_id
        logger.info('send_code_requested', extra={'event':'send_code_requested','trace_id':trace_id})
        # Send code via telethon stub/real
        try:
            from services import telethon_manager
            send_res = await telethon_manager.send_code(phone, trace_id=trace_id, user_id=str(getattr(update.effective_user,'id', '')))
            logger.info('send_code_result', extra={'event':'send_code_result','result':send_res})
        except Exception as e:
            logger.error('send_code_error', extra={'event':'send_code_error','error':str(e),'trace_id':trace_id})
        await update.message.reply_text('📱 شماره ذخیره شد. کد ورود را ارسال کن:', reply_markup=otp_keyboard()); return

    # Text-based OTP entry
    if context.user_data.get('waiting_for_code'):
        if text.isdigit() and 4 <= len(text) <= 8:
            code = text
            phone = context.user_data.get('phone')
            trace_id = context.user_data.get('trace_id') or str(uuid.uuid4())
            from services import telethon_manager
            try:
                result = await telethon_manager.confirm_code(phone, code, trace_id=trace_id)
            except Exception as e:
                result = {"error": str(e)}
            err = result.get('error') if isinstance(result, dict) else None
            ok = not err
            if ok:
                context.user_data.clear()
                # telemetry update: telethon phone/session
                try:
                    from utils.data import load_data, save_data
                    data = load_data() or {}
                    data['telethon_phone'] = phone
                    data['session_status'] = 'ok'
                    save_data(data)
                except Exception:
                    pass
                await update.message.reply_text('✅ ورود موفق.', reply_markup=main_menu()); return
            if err == 'password_needed':
                context.user_data['waiting_for_password'] = True
                await update.message.reply_text('🔐 رمز دو مرحله‌ای لازم است. رمز را ارسال کن.', reply_markup=back_menu()); return
            await update.message.reply_text('❌ کد نامعتبر یا خطا در ورود. دوباره تلاش کن.', reply_markup=otp_keyboard()); return

    # 2FA password entry
    if context.user_data.get('waiting_for_password'):
        pwd = text.strip()
        trace_id = context.user_data.get('trace_id') or str(uuid.uuid4())
        from services import telethon_manager
        res = await telethon_manager.confirm_password(pwd, trace_id=trace_id)
        if res.get('ok'):
            context.user_data.clear()
            try:
                from utils.data import load_data, save_data
                d = load_data() or {}
                d['session_status'] = 'ok'
                save_data(d)
            except Exception:
                pass
            await update.message.reply_text('✅ ورود با رمز 2FA موفق بود.', reply_markup=main_menu()); return
        await update.message.reply_text('❌ رمز 2FA نامعتبر. دوباره تلاش کن.', reply_markup=back_menu()); return
    await update.message.reply_text('پیام دریافت شد.', reply_markup=main_menu())
