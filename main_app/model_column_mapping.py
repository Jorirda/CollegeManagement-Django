from main_app.models import CustomUser, Session, Campus, Course, Student, Teacher, ClassSchedule, LearningRecord, PaymentRecord, RefundRecord

MODEL_COLUMN_MAPPING = {
    'CustomUser': {
        'model': CustomUser,
        'fields': {
            '姓名': 'full_name',
            '邮箱': 'email',
            '性别': 'gender',
            '地址': 'address',
            '电话号码': 'phone_number',
            '用户类型': 'user_type'
        }
    },
    'Student': {
        'model': Student,
        'fields': {
            '学生姓名': 'admin',
            '校区': 'campus',
            '班级': 'course',
            '出生日期': 'date_of_birth',
            '注册日期': 'reg_date',
            '状态': 'status'
        }
    },
    'Teacher': {
        'model': Teacher,
        'fields': {
            '授课老师': 'admin',
            '班级': 'course',
            '校区': 'campus',
            '工作类型': 'work_type'
        }
    },
    'Session': {
        'model': Session,
        'fields': {
            '开始年份': 'start_year',
            '结束年份': 'end_year'
        }
    },
    'Campus': {
        'model': Campus,
        'fields': {
            '校区': 'name',
            '校长': 'principal',
            '校长联系电话': 'principal_contact_number'
        }
    },
    'Course': {
        'model': Course,
        'fields': {
            '班级': 'name',
            '班级概述': 'overview',
            '开始级别': 'level_start',
            '结束级别': 'level_end',
            '图片': 'image'
        }
    },
    'ClassSchedule': {
        'model': ClassSchedule,
        'fields': {
            '班级': 'course',
            '教师': 'teacher',
            '年级': 'grade',
            '开始时间': 'start_time',
            '结束时间': 'end_time',
            '课时': 'lesson_hours',
            '备注': 'remark'
        }
    },
    'LearningRecord': {
        'model': LearningRecord,
        'fields': {
            '日期': 'date',
            '学生': 'student',
            '班级': 'course',
            '教师': 'teacher',
            '班级安排': 'schedule_record',
            '学期': 'semester',
            '开始时间': 'start_time',
            '结束时间': 'end_time',
            '课时': 'lesson_hours',
            '星期': 'day'
        }
    },
    'PaymentRecord': {
        'model': PaymentRecord,
        'fields': {
            '日期': 'date',
            '下次缴费时间\n（班级结束前1月）': 'next_payment_date',
            '学生': 'student',
            '班级': 'course',
            '课时单价': 'lesson_unit_price',
            '折后价格': 'discounted_price',
            '书本费': 'book_costs',
            '其他费用': 'other_fee',
            '应付金额': 'amount_due',
            '缴费': 'amount_paid',
            '支付方式': 'payment_method',
            '状态': 'status',
            '缴费人': 'payee',
            '备注': 'remark',
            '课时': 'lesson_hours',
            '学习记录': 'learning_record'
        }
    },
    'RefundRecord': {
        'model': RefundRecord,
        'fields': {
            '学生': 'student',
            '学习记录': 'learning_records',
            '付款记录': 'payment_records',
            '退款金额': 'refund_amount',
            '已退款金额': 'amount_refunded',
            '退款原因': 'refund_reason'
        }
    }
}
