;;; ============================================================
;;; PDSG-LISP Excel 读取模块
;;; 使用 ActiveX/COM 接口读取 Excel 文件
;;; ============================================================

;;; ------------------------------------------------------------
;;; 通过 ActiveX 读取 Excel 文件
;;; ------------------------------------------------------------
(defun pdsg-read-excel (excel-file sheet-name / excel-app wb ws row col
                        records fields last-row last-col cell-val
                        header-row data-start-row result abort-signal)
  (princ (strcat "\n[INFO] 正在读取 Excel: " excel-file))

  (if (null (findfile excel-file))
    (progn
      (princ (strcat "\n[ERROR] 文件不存在: " excel-file))
      (list)
    )
    (progn
      (setq records (list))
      (setq header-row 1)
      (setq data-start-row 2)
      (setq excel-app nil)
      (setq wb nil)
      (setq abort-signal nil)

      (setq result
        (vl-catch-all-apply
          (function (lambda ()
            (setq excel-app (vlax-create-object "Excel.Application"))
            (if (null excel-app)
              (progn
                (princ "\n[ERROR] 无法启动 Excel，请确保已安装 Microsoft Excel")
                (setq abort-signal t)
              )
            )
            (if (null abort-signal)
              (progn
                (vlax-put-property excel-app 'Visible :vlax-false)

                (princ "\n[INFO] 正在打开工作簿...")
                (setq wb (vlax-invoke-method
                           (vlax-get-property excel-app 'Workbooks)
                           'Open
                           (vlax-make-variant excel-file)))

                (if (null wb)
                  (progn
                    (princ "\n[ERROR] 无法打开工作簿")
                    (setq abort-signal t)
                  )
                )
              )
            )

            (if (and (null abort-signal) wb)
              (progn
                (setq ws (vlax-get-property wb 'Worksheets))
                (if sheet-name
                  (setq ws (vlax-get-property ws 'Item sheet-name))
                  (setq ws (vlax-get-property ws 'Item 1))
                )

                (if (null ws)
                  (progn
                    (princ "\n[ERROR] 无法获取工作表")
                    (setq abort-signal t)
                  )
                )

                (if (null abort-signal)
                  (progn
                    (setq last-row (vlax-get-property
                                      (vlax-get-property ws 'UsedRange)
                                      'Rows
                                      'Count))
                    (setq last-col (vlax-get-property
                                      (vlax-get-property ws 'UsedRange)
                                      'Columns
                                      'Count))

                    (princ (strcat "\n[INFO] 工作表范围: " (itoa last-row) " 行 x "
                                   (itoa last-col) " 列"))

                    (setq fields (list))
                    (setq col 1)
                    (while (<= col last-col)
                      (setq cell-val (vlax-get-property
                                       (vlax-get-property ws 'Cells)
                                       'Item header-row col))
                      (setq cell-val (vlax-variant-value cell-val))
                      (if (and cell-val (/= cell-val ""))
                        (setq fields (append fields (list cell-val)))
                        (setq fields (append fields (list (strcat "Col" (itoa col)))))
                      )
                      (setq col (1+ col))
                    )

                    (princ "\n[INFO] 标题行:")
                    (foreach f fields
                      (princ (strcat "\n  " f))
                    )

                    (setq row data-start-row)
                    (while (<= row last-row)
                      (setq record (list))
                      (setq col 1)
                      (setq has-data nil)

                      (while (<= col last-col)
                        (setq cell-val (vlax-get-property
                                          (vlax-get-property ws 'Cells)
                                          'Item row col))
                        (setq cell-val (vlax-variant-value cell-val))
                        (if cell-val
                          (progn
                            (setq cell-val (vl-to-str cell-val))
                            (setq has-data t)
                          )
                          (setq cell-val "")
                        )
                        (setq record (append record (list (cons (nth (1- col) fields) cell-val))))
                        (setq col (1+ col))
                      )

                      (if has-data
                        (progn
                          (setq record (append record (list (cons "row" row))))
                          (setq records (append records (list record)))
                        )
                      )

                      (setq row (1+ row))
                    )

                    (princ (strcat "\n[INFO] 读取 " (itoa (length records)) " 条记录"))
                  )
                )
              )
            )
          ))
        )
      )

      ;; 安全释放 COM 对象
      (if wb
        (vl-catch-all-apply
          (function (lambda ()
            (vlax-invoke-method wb 'Close :vlax-false)
          ))
        )
      )
      (if excel-app
        (vl-catch-all-apply
          (function (lambda ()
            (vlax-invoke-method excel-app 'Quit)
            (vlax-release-object excel-app)
          ))
        )
      )

      records
    )
  )
)

;;; ------------------------------------------------------------
;;; 辅助函数：VL 变量转字符串
;;; ------------------------------------------------------------
(defun vl-to-str (val / type-tag)
  (if (null val)
    ""
    (progn
      (setq type-tag (type val))
      (cond
        ((= type-tag 'STR) val)
        ((= type-tag 'INT) (itoa val))
        ((= type-tag 'REAL) (rtos val 2 6))
        ((= type-tag 'FILE) (vl-filename-base val))
        (T (vl-princ-to-string val))
      )
    )
  )
)

;;; ------------------------------------------------------------
;;; 通过 CSV 方式读取（备选方案）
;;; ------------------------------------------------------------
(defun pdsg-read-excel-csv (excel-file / csv-file)
  (princ "\n[INFO] 使用 CSV 转换方式读取...")
  (princ "\n[INFO] 请先将 Excel 文件另存为 CSV 格式")

  (setq csv-file (getfile "选择对应的 CSV 文件" "CSV" "选择"))
  (if (null csv-file)
    (list)
    (pdsg-read-csv csv-file)
  )
)

;;; ------------------------------------------------------------
;;; 校验回路数据
;;; ------------------------------------------------------------
(defun pdsg-validate-excel-records (records / valid-list errors rec is-valid)
  (setq valid-list (list))
  (setq errors (list))

  (foreach rec records
    (setq is-valid t)

    ;; 检查回路名称
    (if (or (null (cdr (assoc "circuit_name" rec)))
            (= (cdr (assoc "circuit_name" rec)) ""))
      (progn
        (setq is-valid nil)
        (setq errors (append errors (list
          (cons (cdr (assoc "row" rec)) "缺少回路名称"))))
      )
    )

    ;; 检查断路器类型
    (if (or (null (cdr (assoc "breaker_type" rec)))
            (= (cdr (assoc "breaker_type" rec)) ""))
      (progn
        (setq is-valid nil)
        (setq errors (append errors (list
          (cons (cdr (assoc "row" rec)) "缺少断路器类型"))))
      )
    )

    ;; 检查额定电流
    (if (or (null (cdr (assoc "breaker_rating" rec)))
            (= (cdr (assoc "breaker_rating" rec)) ""))
      (progn
        (setq is-valid nil)
        (setq errors (append errors (list
          (cons (cdr (assoc "row" rec)) "缺少额定电流"))))
      )
    )

    (if is-valid
      (setq valid-list (append valid-list (list rec)))
    )
  )

  (princ (strcat "\n[INFO] 校验完成: 有效 " (itoa (length valid-list))
                 " / 错误 " (itoa (length errors))))
  (list valid-list errors)
)

;;; ------------------------------------------------------------
;;; Excel 导入命令
;;; ------------------------------------------------------------
(defun c:PDSG_IMPORT ( / excel-file sheet-name records valid-errors choice)
  (princ "\n========================================")
  (princ "\n  PDSG Excel 数据导入")
  (princ "\n========================================")

  (princ "\n\n选择数据源:")
  (princ "\n  1 - 直接读取 Excel 文件 (需要安装 Microsoft Excel)")
  (princ "\n  2 - 读取 CSV 文件 (推荐)")
  (princ "")

  (setq choice (getstring "\n请选择 (1/2): "))

  (if (= choice "1")
    (progn
      ;; 直接读取 Excel
      (setq excel-file (getfile "选择 Excel 文件" "xls;xlsx" "选择"))
      (if excel-file
        (progn
          (setq sheet-name (getstring T "\n请输入工作表名称 (留空使用第一个): "))
          (if (= sheet-name "") (setq sheet-name nil))
          (setq records (pdsg-read-excel excel-file sheet-name))
          (if (and records (> (length records) 0))
            (progn
              (setq valid-errors (pdsg-validate-excel-records records))
              (princ (strcat "\n\n[DONE] 导入完成: " (itoa (length records)) " 条记录"))
              (setq *pdsg-imported-records* records)
            )
            (princ "\n[ERROR] 未读取到有效数据")
          )
        )
        (princ "\n[INFO] 已取消")
      )
    )
    (progn
      ;; 读取 CSV
      (setq excel-file (getfile "选择 CSV 文件" "csv" "选择"))
      (if excel-file
        (progn
          (setq records (pdsg-read-csv excel-file))
          (if (and records (> (length records) 0))
            (progn
              (princ (strcat "\n\n[DONE] 导入完成: " (itoa (length records)) " 条记录"))
              (setq *pdsg-imported-records* records)
            )
            (princ "\n[ERROR] 未读取到有效数据")
          )
        )
        (princ "\n[INFO] 已取消")
      )
    )
  )

  (princ)
)

(princ "\n[PDSG-LISP Excel 模块已加载]")
