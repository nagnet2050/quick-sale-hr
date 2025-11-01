/**
 * نظام دردشة WhatsApp
 * يدعم النصوص، الصوتيات، الصور، والتسجيل الصوتي
 */

let currentConversationId = null;
let mediaRecorder = null;
let audioChunks = [];
let recordingStartTime = null;
let recordingInterval = null;
let autoRefreshInterval = null;

// ==================== تحميل البيانات ====================

// تحميل المحادثات
function loadConversations() {
    fetch('/api/whatsapp/conversations')
        .then(response => response.json())
        .then(conversations => {
            const container = document.getElementById('conversations-list');
            container.innerHTML = '';
            
            if (conversations.length === 0) {
                container.innerHTML = `
                    <div class="text-center text-muted p-3">
                        <i class="bi bi-chat-dots fs-1"></i>
                        <p class="mt-2">لا توجد محادثات حالياً</p>
                    </div>
                `;
                return;
            }
            
            conversations.forEach(conv => {
                const unreadBadge = conv.unread_count > 0 
                    ? `<span class="badge bg-success">${conv.unread_count}</span>` 
                    : '';
                
                const convElement = document.createElement('div');
                convElement.className = 'conversation-item';
                convElement.onclick = () => loadConversation(conv.id);
                convElement.innerHTML = `
                    <div class="d-flex align-items-center">
                        <div class="avatar me-2">
                            <i class="bi bi-person-circle fs-3"></i>
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between">
                                <strong>${conv.customer_name || conv.customer_phone}</strong>
                                ${unreadBadge}
                            </div>
                            <div class="text-muted small">${conv.customer_phone}</div>
                            <div class="text-muted small text-truncate">${conv.last_message || 'لا توجد رسائل'}</div>
                        </div>
                    </div>
                `;
                
                container.appendChild(convElement);
            });
        })
        .catch(error => {
            console.error('Error loading conversations:', error);
            document.getElementById('conversations-list').innerHTML = `
                <div class="alert alert-danger m-2">
                    خطأ في تحميل المحادثات
                </div>
            `;
        });
}

// تحميل محادثة محددة
function loadConversation(conversationId) {
    currentConversationId = conversationId;
    
    // إظهار رأس الدردشة ومنطقة الإدخال
    document.getElementById('chat-header').style.display = 'flex';
    document.getElementById('input-area').style.display = 'flex';
    
    fetch(`/api/whatsapp/messages/${conversationId}`)
        .then(response => response.json())
        .then(messages => {
            displayMessages(messages);
            
            // تحديث معلومات العميل في الرأس
            if (messages.length > 0) {
                const firstMessage = messages[0];
                fetch(`/api/whatsapp/conversations`)
                    .then(res => res.json())
                    .then(convs => {
                        const conv = convs.find(c => c.id === conversationId);
                        if (conv) {
                            document.getElementById('customer-name').textContent = conv.customer_name || conv.customer_phone;
                            document.getElementById('customer-phone').textContent = conv.customer_phone;
                        }
                    });
            }
        })
        .catch(error => {
            console.error('Error loading messages:', error);
            document.getElementById('messages-container').innerHTML = `
                <div class="alert alert-danger m-3">
                    خطأ في تحميل الرسائل
                </div>
            `;
        });
}

// عرض الرسائل
function displayMessages(messages) {
    const container = document.getElementById('messages-container');
    container.innerHTML = '';
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted p-3">
                <p>لا توجد رسائل بعد</p>
            </div>
        `;
        return;
    }
    
    messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.direction}`;
        
        let content = '';
        const timestamp = new Date(msg.timestamp).toLocaleTimeString('ar-EG', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        switch(msg.message_type) {
            case 'text':
                content = `
                    <div class="message-bubble">
                        <div class="message-text">${escapeHtml(msg.message_content)}</div>
                        <div class="message-time">${timestamp}</div>
                    </div>
                `;
                break;
                
            case 'audio':
                content = `
                    <div class="message-bubble">
                        <div class="audio-message">
                            <audio controls>
                                <source src="${msg.audio_url}" type="audio/mpeg">
                                متصفحك لا يدعم تشغيل الصوت
                            </audio>
                        </div>
                        <div class="message-time">${timestamp}</div>
                    </div>
                `;
                break;
                
            case 'image':
                content = `
                    <div class="message-bubble">
                        <div class="image-message">
                            <img src="${msg.image_url}" alt="صورة" class="img-fluid rounded" 
                                 onclick="window.open('${msg.image_url}', '_blank')">
                            ${msg.caption ? `<div class="mt-2">${escapeHtml(msg.caption)}</div>` : ''}
                        </div>
                        <div class="message-time">${timestamp}</div>
                    </div>
                `;
                break;
                
            case 'document':
                content = `
                    <div class="message-bubble">
                        <div class="document-message">
                            <i class="bi bi-file-earmark-text fs-1"></i>
                            <a href="${msg.document_url}" target="_blank" class="btn btn-sm btn-link">
                                تحميل المستند
                            </a>
                        </div>
                        <div class="message-time">${timestamp}</div>
                    </div>
                `;
                break;
        }
        
        messageDiv.innerHTML = content;
        container.appendChild(messageDiv);
    });
    
    // التمرير لآخر رسالة
    container.scrollTop = container.scrollHeight;
}

// ==================== إرسال الرسائل ====================

// إرسال رسالة نصية
function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message || !currentConversationId) {
        return;
    }
    
    // تعطيل زر الإرسال
    const sendBtn = document.querySelector('.send-btn');
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    
    fetch('/api/whatsapp/send-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            conversation_id: currentConversationId,
            message: message
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            input.value = '';
            loadConversation(currentConversationId);
            loadConversations(); // تحديث قائمة المحادثات
        } else {
            alert('فشل إرسال الرسالة: ' + (result.error || 'خطأ غير معروف'));
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        alert('خطأ في إرسال الرسالة');
    })
    .finally(() => {
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<i class="bi bi-send-fill"></i>';
    });
}

// معالجة ضغط Enter
function handleEnterKey(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// ==================== التسجيل الصوتي ====================

// بدء تسجيل صوتي
function startAudioRecording() {
    if (!currentConversationId) {
        alert('الرجاء اختيار محادثة أولاً');
        return;
    }
    
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg' });
                sendAudioMessage(audioBlob);
                
                // إيقاف جميع المسارات
                stream.getTracks().forEach(track => track.stop());
            };
            
            mediaRecorder.start();
            
            // إظهار واجهة التسجيل
            document.getElementById('input-area').style.display = 'none';
            document.getElementById('audio-recorder').style.display = 'flex';
            
            // بدء عداد الوقت
            recordingStartTime = Date.now();
            recordingInterval = setInterval(updateRecordingTime, 100);
        })
        .catch(error => {
            console.error('Error accessing microphone:', error);
            alert('لا يمكن الوصول إلى الميكروفون. الرجاء السماح بالوصول.');
        });
}

// إيقاف التسجيل
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        clearInterval(recordingInterval);
        
        // إخفاء واجهة التسجيل
        document.getElementById('audio-recorder').style.display = 'none';
        document.getElementById('input-area').style.display = 'flex';
    }
}

// إلغاء التسجيل
function cancelRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        audioChunks = [];
        clearInterval(recordingInterval);
        
        // إخفاء واجهة التسجيل
        document.getElementById('audio-recorder').style.display = 'none';
        document.getElementById('input-area').style.display = 'flex';
    }
}

// تحديث وقت التسجيل
function updateRecordingTime() {
    const elapsed = Date.now() - recordingStartTime;
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    document.getElementById('recording-time').textContent = 
        `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// إرسال رسالة صوتية
function sendAudioMessage(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.mp3');
    formData.append('conversation_id', currentConversationId);
    
    fetch('/api/whatsapp/send-audio', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            loadConversation(currentConversationId);
            loadConversations();
        } else {
            alert('فشل إرسال الرسالة الصوتية: ' + (result.error || 'خطأ غير معروف'));
        }
    })
    .catch(error => {
        console.error('Error sending audio:', error);
        alert('خطأ في إرسال الرسالة الصوتية');
    });
}

// ==================== الملفات ====================

// معالجة اختيار ملف صوتي
function handleAudioFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        sendAudioMessage(file);
    }
}

// معالجة اختيار صورة
function handleImageFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        // TODO: إضافة دعم إرسال الصور
        alert('سيتم إضافة دعم إرسال الصور قريباً');
    }
}

// ==================== القوالب ====================

// استخدام قالب جاهز
function useTemplate() {
    fetch('/api/whatsapp/templates')
        .then(response => response.json())
        .then(templates => {
            const list = document.getElementById('templates-list');
            list.innerHTML = '';
            
            if (templates.length === 0) {
                list.innerHTML = '<p class="text-muted">لا توجد قوالب متاحة</p>';
                return;
            }
            
            templates.forEach(template => {
                const templateDiv = document.createElement('div');
                templateDiv.className = 'template-item p-2 border rounded mb-2 cursor-pointer';
                templateDiv.onclick = () => selectTemplate(template);
                templateDiv.innerHTML = `
                    <strong>${template.name}</strong>
                    <p class="text-muted small mb-0">${template.content}</p>
                `;
                list.appendChild(templateDiv);
            });
            
            // إظهار المودال
            const modal = new bootstrap.Modal(document.getElementById('templates-modal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error loading templates:', error);
            alert('خطأ في تحميل القوالب');
        });
}

// اختيار قالب
function selectTemplate(template) {
    document.getElementById('message-input').value = template.content;
    bootstrap.Modal.getInstance(document.getElementById('templates-modal')).hide();
}

// ==================== مساعدات ====================

// تنظيف HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// تحديث الدردشة
function refreshChat() {
    if (currentConversationId) {
        loadConversation(currentConversationId);
    }
    loadConversations();
}

// البحث في المحادثات
document.getElementById('search-conversations')?.addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const conversations = document.querySelectorAll('.conversation-item');
    
    conversations.forEach(conv => {
        const text = conv.textContent.toLowerCase();
        conv.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
});

// ==================== التحديث التلقائي ====================

// بدء التحديث التلقائي
function startAutoRefresh() {
    // تحديث كل 5 ثواني
    autoRefreshInterval = setInterval(() => {
        if (currentConversationId) {
            loadConversation(currentConversationId);
        }
        loadConversations();
    }, 5000);
}

// إيقاف التحديث التلقائي
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
}

// ==================== التهيئة ====================

// التحميل الأولي عند فتح الصفحة
document.addEventListener('DOMContentLoaded', function() {
    loadConversations();
    startAutoRefresh();
    
    // إيقاف التحديث عند مغادرة الصفحة
    window.addEventListener('beforeunload', stopAutoRefresh);
});
