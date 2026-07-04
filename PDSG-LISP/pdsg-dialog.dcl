// ============================================================
// PDSG-LISP 主界面 DCL
// 配电系统图自动生成程序 - 图形界面
// ============================================================

pdsg_main : dialog {
    key = "title";
    label = "PDSG 配电系统图自动生成";
    initial_focus = "file_path";

    // 标题区域
    row {
        text {
            label = "PDSG";
            width = 8;
            alignment = left;
        }
        spacer_0;
        text {
            key = "version";
            label = "v1.0.0";
            width = 10;
            alignment = right;
        }
    }
    spacer_0;

    // 分组框：数据源设置
    : boxed_column {
        label = " 数据源设置 ";

        : row {
            : popup_list {
                key = "data_source";
                label = "数据来源:";
                list = "Excel 文件\nCSV 文件";
                value = "1";
                width = 30;
            }
        }

        : row {
            : edit_box {
                key = "file_path";
                label = "文件路径:";
                width = 45;
                edit_width = 40;
                edit_limit = 256;
            }
            : button {
                key = "browse_btn";
                label = "浏览...";
                width = 10;
            }
        }

        : row {
            : edit_box {
                key = "sheet_name";
                label = "工作表:";
                width = 30;
                edit_width = 25;
                edit_limit = 64;
            }
            : edit_box {
                key = "start_row";
                label = "起始行:";
                width = 15;
                edit_width = 10;
                edit_limit = 5;
                value = "2";
            }
        }
    }
    spacer_0;

    // 分组框：图纸设置
    : boxed_column {
        label = " 图纸设置 ";

        : row {
            : popup_list {
                key = "paper_size";
                label = "图纸尺寸:";
                list = "A3 (420x297)\nA2 (594x420)\nA1 (841x594)\nA0 (1189x841)";
                value = "0";
                width = 25;
            }
            : edit_box {
                key = "bus_y";
                label = "母线Y坐标 (mm):";
                width = 22;
                edit_width = 15;
                edit_limit = 10;
                value = "220";
            }
        }

        : row {
            : edit_box {
                key = "spacing";
                label = "回路间距 (mm):";
                width = 22;
                edit_width = 15;
                edit_limit = 10;
                value = "35";
            }
            : edit_box {
                key = "start_x";
                label = "起始X坐标 (mm):";
                width = 22;
                edit_width = 15;
                edit_limit = 10;
                value = "20";
            }
        }
    }
    spacer_0;

    // 分组框：输出设置
    : boxed_column {
        label = " 输出设置 ";

        : row {
            : edit_box {
                key = "output_path";
                label = "输出目录:";
                width = 45;
                edit_width = 40;
                edit_limit = 256;
            }
            : button {
                key = "output_browse";
                label = "浏览...";
                width = 10;
            }
        }

        : row {
            : edit_box {
                key = "output_name";
                label = "文件名:";
                width = 30;
                edit_width = 25;
                edit_limit = 64;
                value = "配电系统图";
            }
            : checkbox {
                key = "auto_save";
                label = "自动保存";
                value = "1";
            }
        }
    }
    spacer_0;

    // 分组框：图块设置
    : boxed_column {
        label = " 图块设置 ";

        : row {
            : checkbox {
                key = "use_standard_blocks";
                label = "使用标准图块";
                value = "1";
            }
            : checkbox {
                key = "create_missing";
                label = "自动创建缺失图块";
                value = "1";
            }
        }

        : row {
            : edit_box {
                key = "block_scale";
                label = "图块比例:";
                width = 18;
                edit_width = 10;
                edit_limit = 10;
                value = "1.0";
            }
            : edit_box {
                key = "block_rotation";
                label = "旋转角度 (°):";
                width = 18;
                edit_width = 10;
                edit_limit = 10;
                value = "0";
            }
        }
    }
    spacer_0;

    // 操作按钮
    : row {
        : button {
            key = "preview";
            label = "预览数据";
            width = 14;
        }
        : button {
            key = "dry_run";
            label = "校验数据";
            width = 14;
        }
        : button {
            key = "generate";
            label = "生成图纸";
            width = 14;
            is_default = true;
        }
        : button {
            key = "cancel";
            label = "退出";
            width = 14;
            is_cancel = true;
        }
    }
    spacer_0;

    // 状态栏
    : row {
        : text {
            key = "status";
            label = "就绪";
            width = 45;
        }
        : text {
            key = "record_count";
            label = "记录: 0";
            width = 15;
            alignment = right;
        }
    }
}

// 预览对话框
pdsg_preview : dialog {
    key = "preview_title";
    label = "数据预览";

    : text {
        key = "preview_list";
        width = 60;
        height = 18;
    }

    spacer_0;

    : row {
        : text {
            key = "preview_info";
            label = "";
            width = 40;
        }
        : button {
            key = "preview_close";
            label = "关闭";
            width = 12;
            is_cancel = true;
        }
    }
}

// 错误报告对话框
pdsg_errors : dialog {
    key = "error_title";
    label = "数据校验错误";

    : text {
        key = "error_list";
        width = 60;
        height = 12;
    }

    spacer_0;

    : row {
        : text {
            key = "error_summary";
            label = "";
            width = 40;
        }
        : button {
            key = "error_close";
            label = "关闭";
            width = 12;
            is_cancel = true;
        }
    }
}

// 关于对话框
pdsg_about : dialog {
    key = "about_title";
    label = "关于 PDSG-LISP";

    : row {
        : column {
            : text {
                label = "PDSG-LISP";
                width = 20;
            }
            : text {
                key = "about_version";
                label = "版本: 1.0.0";
                width = 20;
            }
        }
        : column {
            : text {
                label = "配电系统图自动生成程序";
                width = 30;
            }
            : text {
                label = "转换自 PDSG.NET";
                width = 30;
            }
        }
    }

    spacer_0;

    : text {
        label = "功能: 读取Excel/CSV → 映射图块 → 生成配电系统图";
        width = 50;
    }

    spacer_0;

    : row {
        : text {
            label = "Copyright 2026";
            width = 20;
        }
        : button {
            key = "about_close";
            label = "确定";
            width = 12;
            is_default = true;
            is_cancel = true;
        }
    }
}
