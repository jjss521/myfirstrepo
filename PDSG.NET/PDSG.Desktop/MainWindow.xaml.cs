using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;
using PDSG.Core.Config;
using PDSG.Core.Models;
using PDSG.Core.Mapping;

namespace PDSG.Desktop;

public partial class MainWindow : Window
{
    private AppConfig? _cfg;
    private List<CircuitRecord> _records = new();
    private List<ErrorRecord> _errors = new();
    private CancellationTokenSource? _cts;

    public MainWindow()
    {
        InitializeComponent();
        LoadDefaultConfig();
    }

    private void LoadDefaultConfig()
    {
        try
        {
            if (File.Exists("config.yaml"))
            {
                _cfg = ConfigLoader.Load("config.yaml");
                ApplyConfigToUI();
                Log("配置已加载: config.yaml");
            }
        }
        catch (Exception ex)
        {
            Log($"配置加载失败: {ex.Message}");
        }
    }

    private void ApplyConfigToUI()
    {
        if (_cfg == null) return;

        txtSheetName.Text = _cfg.Excel.SheetName;
        txtDefaultBreaker.Text = _cfg.Excel.DefaultBreakerModel;
        txtBlockLibPath.Text = _cfg.BlockLibrary.Path;
        txtBlockCatalogPath.Text = _cfg.BlockLibrary.Catalog;
        txtDefaultBlock.Text = _cfg.BlockLibrary.DefaultBlock;
        txtSpacing.Text = _cfg.Layout.HorizontalSpacing.ToString();
        txtBusX.Text = _cfg.Layout.BusX.ToString();
        txtBusY.Text = _cfg.Layout.BusY.ToString();
        txtOutputPath.Text = _cfg.Output.DwgPath;
    }

    private AppConfig BuildConfigFromUI()
    {
        var cfg = _cfg ?? new AppConfig();

        cfg.Excel.SheetName = txtSheetName.Text;
        cfg.Excel.DefaultBreakerModel = txtDefaultBreaker.Text;
        cfg.Excel.FormatAutoDetect = chkAutoDetect.IsChecked == true;
        cfg.BlockLibrary.Path = txtBlockLibPath.Text;
        cfg.BlockLibrary.Catalog = txtBlockCatalogPath.Text;
        cfg.BlockLibrary.DefaultBlock = txtDefaultBlock.Text;

        if (double.TryParse(txtSpacing.Text, out var spacing))
            cfg.Layout.HorizontalSpacing = spacing;
        if (double.TryParse(txtBusX.Text, out var busX))
            cfg.Layout.BusX = busX;
        if (double.TryParse(txtBusY.Text, out var busY))
            cfg.Layout.BusY = busY;

        if (!string.IsNullOrEmpty(txtOutputPath.Text))
            cfg.Output.DwgPath = txtOutputPath.Text;

        return cfg;
    }

    private void BtnBrowseExcel_Click(object sender, RoutedEventArgs e)
    {
        var dlg = new OpenFileDialog
        {
            Filter = "Excel 文件|*.xlsx;*.xls|所有文件|*.*",
            Title = "选择 Excel 回路清单"
        };
        if (dlg.ShowDialog() == true)
        {
            txtExcelPath.Text = dlg.FileName;
            Log($"已选择: {dlg.FileName}");
        }
    }

    private void BtnBrowseOutput_Click(object sender, RoutedEventArgs e)
    {
        var dlg = new SaveFileDialog
        {
            Filter = "DWG 文件|*.dwg",
            Title = "选择输出路径",
            FileName = "system.dwg"
        };
        if (dlg.ShowDialog() == true)
        {
            txtOutputPath.Text = dlg.FileName;
        }
    }

    private void BtnBrowseBlockLib_Click(object sender, RoutedEventArgs e)
    {
        var dlg = new OpenFileDialog
        {
            Filter = "DWG 文件|*.dwg",
            Title = "选择图块库文件"
        };
        if (dlg.ShowDialog() == true)
            txtBlockLibPath.Text = dlg.FileName;
    }

    private void BtnBrowseBlockCatalog_Click(object sender, RoutedEventArgs e)
    {
        var dlg = new OpenFileDialog
        {
            Filter = "YAML 文件|*.yaml;*.yml",
            Title = "选择图块目录文件"
        };
        if (dlg.ShowDialog() == true)
            txtBlockCatalogPath.Text = dlg.FileName;
    }

    private void BtnLoadPreview_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrEmpty(txtExcelPath.Text))
        {
            MessageBox.Show("请先选择 Excel 文件", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        try
        {
            var cfg = BuildConfigFromUI();
            var (records, errors) = Core.Excel.ExcelReader.ReadAndValidate(txtExcelPath.Text, cfg.Excel);

            _records = records;
            _errors = errors;

            dgPreview.ItemsSource = records.Select(r => new
            {
                行号 = r.RowNumber,
                回路编号 = r.CircuitId,
                回路名称 = r.CircuitName,
                负荷类型 = r.LoadType.ToChinese(),
                功率_kW = r.RatedPowerKw,
                电流_A = r.RatedCurrentA,
                断路器 = r.BreakerModel,
                极数 = r.BreakerPoles,
                脱扣器_A = r.BreakerTripCurrentA,
                CT变比 = r.CtRatio,
                电缆 = $"{r.CableType} {r.CableSection}"
            }).ToList();

            txtRecordCount.Text = $"记录数: {records.Count}";
            txtErrorCount.Text = errors.Count > 0 ? $"错误数: {errors.Count}" : "";
            txtPreviewInfo.Text = $"有效 {records.Count} / 跳过 {errors.Count}";
            tabMain.SelectedIndex = 1;
            Log($"数据加载完成: 有效 {records.Count}, 跳过 {errors.Count}");
        }
        catch (Exception ex)
        {
            MessageBox.Show($"加载失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            Log($"错误: {ex.Message}");
        }
    }

    private async void BtnDryRun_Click(object sender, RoutedEventArgs e)
    {
        if (!ValidateInput()) return;

        SetRunning(true);
        Log("=== DRY-RUN 模式 ===");

        try
        {
            var cfg = BuildConfigFromUI();
            var (records, errors) = await Task.Run(() =>
                Core.Excel.ExcelReader.ReadAndValidate(txtExcelPath.Text, cfg.Excel));

            Log($"Excel 读取: 有效 {records.Count}, 跳过 {errors.Count}");

            if (records.Count == 0)
            {
                Log("无有效回路数据");
                return;
            }

            var catalog = Core.Mapping.BlockLibrary.LoadCatalog(cfg.BlockLibrary.Catalog);
            var (mapped, warnings) = Core.Mapping.BlockMapper.MapCircuits(records, cfg.BlockMapping, catalog);
            Core.Mapping.AttributeBuilder.BuildAllAttributes(mapped, catalog);
            var layout = Core.Layout.LayoutEngine.Compute(mapped, cfg.Layout, cfg.Sort);

            Log($"图纸幅面: {layout.PaperSize.Name} ({layout.PaperSize.Width}x{layout.PaperSize.Height}mm)");
            Log($"回路数: {layout.Placements.Count}");
            Log($"母线: X={layout.BusLine.XStart:F1}~{layout.BusLine.XEnd:F1}, Y={layout.BusLine.BusY:F1}");

            foreach (var p in layout.Placements.Take(5))
                Log($"  {p.CircuitId} @ ({p.X:F1}, {p.Y:F1}) block={p.BlockName}");
            if (layout.Placements.Count > 5)
                Log($"  ... 共 {layout.Placements.Count} 个回路");

            txtStatus.Text = $"Dry-run 完成: {layout.Placements.Count} 个回路";
        }
        catch (Exception ex)
        {
            Log($"错误: {ex.Message}");
            txtStatus.Text = "失败";
        }
        finally
        {
            SetRunning(false);
        }
    }

    private async void BtnGenerate_Click(object sender, RoutedEventArgs e)
    {
        if (!ValidateInput()) return;

        SetRunning(true);
        Log("=== 开始生成 DWG ===");
        var sw = Stopwatch.StartNew();

        try
        {
            var cfg = BuildConfigFromUI();
            var (records, errors) = await Task.Run(() =>
                Core.Excel.ExcelReader.ReadAndValidate(txtExcelPath.Text, cfg.Excel));

            Log($"Excel 读取完成: {records.Count} 个回路");

            var catalog = Core.Mapping.BlockLibrary.LoadCatalog(cfg.BlockLibrary.Catalog);
            var (mapped, warnings) = Core.Mapping.BlockMapper.MapCircuits(records, cfg.BlockMapping, catalog);
            Core.Mapping.AttributeBuilder.BuildAllAttributes(mapped, catalog);
            var layout = Core.Layout.LayoutEngine.Compute(mapped, cfg.Layout, cfg.Sort);

            Log($"布局计算完成: {layout.Placements.Count} 个回路, 图幅 {layout.PaperSize.Name}");
            Log("正在连接 AutoCAD 并绘图...");

            await Task.Run(() =>
            {
                using var drawer = new PDSG.AutoCAD.Drawing.CadDrawer();
                drawer.Connect();
                drawer.Draw(layout);
                drawer.SaveAs(cfg.Output.DwgPath);
            });

            sw.Stop();
            Log($"生成完成 ({sw.Elapsed.TotalSeconds:F1}s): 保存到 {cfg.Output.DwgPath}");
            txtStatus.Text = $"完成 ({sw.Elapsed.TotalSeconds:F1}s)";

            // 生成报告
            try
            {
                Core.Report.ReportGenerator.Generate(
                    errors, mapped, warnings,
                    txtExcelPath.Text, cfg.Output.ReportPath,
                    layout.Placements);
                Log($"报告已生成: {cfg.Output.ReportPath}");
            }
            catch (Exception ex)
            {
                Log($"报告生成失败: {ex.Message}");
            }
        }
        catch (Exception ex)
        {
            sw.Stop();
            Log($"错误 ({sw.Elapsed.TotalSeconds:F1}s): {ex.Message}");
            txtStatus.Text = "失败";
        }
        finally
        {
            SetRunning(false);
        }
    }

    private void BtnStop_Click(object sender, RoutedEventArgs e)
    {
        _cts?.Cancel();
        Log("已取消");
    }

    private bool ValidateInput()
    {
        if (string.IsNullOrEmpty(txtExcelPath.Text))
        {
            MessageBox.Show("请先选择 Excel 文件", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
            return false;
        }
        if (!File.Exists(txtExcelPath.Text))
        {
            MessageBox.Show("Excel 文件不存在", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            return false;
        }
        return true;
    }

    private void SetRunning(bool running)
    {
        btnDryRun.IsEnabled = !running;
        btnGenerate.IsEnabled = !running;
        btnStop.IsEnabled = running;
        txtStatus.Text = running ? "运行中..." : "就绪";
        txtTime.Text = DateTime.Now.ToString("HH:mm:ss");
    }

    private void Log(string message)
    {
        var line = $"[{DateTime.Now:HH:mm:ss}] {message}\n";
        txtLog.AppendText(line);
        txtLog.ScrollToEnd();
        txtStatusBar.Text = message;
    }

    // ================================================================
    // 图块管理
    // ================================================================

    private BlockManager? _blockManager;
    private List<BlockDisplayInfo> _blockDisplayList = new();

    private void BtnLoadCatalog_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var catalogPath = txtBlockCatalogPath.Text;
            if (string.IsNullOrEmpty(catalogPath))
            {
                MessageBox.Show("请先在配置中指定图块目录路径", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            _blockManager = BlockManager.Load(catalogPath);
            RefreshBlockDisplay();
            txtBlockStatus.Text = $"已加载: {Path.GetFileName(catalogPath)}";
            txtBlockCount.Text = $"{_blockManager.Blocks.Count} 个图块";
            Log($"图块目录已加载: {_blockManager.Blocks.Count} 个图块");
        }
        catch (Exception ex)
        {
            MessageBox.Show($"加载失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void BtnRefreshBlocks_Click(object sender, RoutedEventArgs e)
    {
        if (_blockManager == null)
        {
            MessageBox.Show("请先加载图块目录", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        try
        {
            using var editor = new PDSG.AutoCAD.Drawing.BlockEditor();
            editor.Connect();
            var drawingNames = editor.GetCircuitBlockNames();

            foreach (var item in _blockDisplayList)
            {
                item.ExistsInDrawing = drawingNames.Contains(item.Name);
            }

            dgBlocks.ItemsSource = null;
            dgBlocks.ItemsSource = _blockDisplayList;
            txtBlockStatus.Text = $"图形中找到 {drawingNames.Count} 个回路图块";
            Log($"已刷新图形块状态");
        }
        catch (Exception ex)
        {
            MessageBox.Show($"刷新失败: {ex.Message}\n请确认 AutoCAD 已启动并打开了文档", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void BtnValidateBlocks_Click(object sender, RoutedEventArgs e)
    {
        if (_blockManager == null)
        {
            MessageBox.Show("请先加载图块目录", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        try
        {
            using var editor = new PDSG.AutoCAD.Drawing.BlockEditor();
            editor.Connect();
            var result = editor.ValidateCatalog(_blockManager);

            string msg = result.IsValid
                ? "图块目录与图形完全一致"
                : $"发现不一致:\n  缺失: {string.Join(", ", result.MissingInDrawing)}\n  多余: {string.Join(", ", result.NotInCatalog)}";

            MessageBox.Show(msg, result.IsValid ? "验证通过" : "验证失败",
                MessageBoxButton.OK,
                result.IsValid ? MessageBoxImage.Information : MessageBoxImage.Warning);

            Log($"复核完成: 有效={result.IsValid}, 缺失={result.MissingInDrawing.Count}, 多余={result.NotInCatalog.Count}");
        }
        catch (Exception ex)
        {
            MessageBox.Show($"复核失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void BtnCreateBlock_Click(object sender, RoutedEventArgs e)
    {
        if (_blockManager == null)
        {
            MessageBox.Show("请先加载图块目录", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var dialog = new CreateBlockDialog();
        if (dialog.ShowDialog() == true)
        {
            try
            {
                // 在 AutoCAD 中创建
                using var editor = new PDSG.AutoCAD.Drawing.BlockEditor();
                editor.Connect();
                editor.CreateBlock(dialog.BlockName, dialog.Description);
                Log($"图块已创建: {dialog.BlockName}");

                // 更新目录
                _blockManager.AddBlock(new BlockDefinition
                {
                    Name = dialog.BlockName,
                    Description = dialog.Description
                });
                _blockManager.Save();
                RefreshBlockDisplay();
                txtBlockCount.Text = $"{_blockManager.Blocks.Count} 个图块";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"创建失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    private void BtnImportDwg_Click(object sender, RoutedEventArgs e)
    {
        if (_blockManager == null)
        {
            MessageBox.Show("请先加载图块目录", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var dlg = new OpenFileDialog
        {
            Filter = "DWG 文件|*.dwg|所有文件|*.*",
            Title = "选择要导入图块的 DWG 文件",
            Multiselect = true
        };

        if (dlg.ShowDialog() == true)
        {
            try
            {
                using var editor = new PDSG.AutoCAD.Drawing.BlockEditor();
                editor.Connect();

                int totalImported = 0;
                foreach (var file in dlg.FileNames)
                {
                    int imported = editor.ImportBlocksFromDwg(file);
                    totalImported += imported;
                    Log($"从 {Path.GetFileName(file)} 导入 {imported} 个图块");
                }

                // 刷新目录
                var drawingNames = editor.GetCircuitBlockNames();
                foreach (var name in drawingNames)
                {
                    if (_blockManager.Find(name) == null)
                    {
                        _blockManager.AddBlock(new BlockDefinition
                        {
                            Name = name,
                            Description = $"从 DWG 导入"
                        });
                    }
                }
                _blockManager.Save();
                RefreshBlockDisplay();

                MessageBox.Show($"已导入 {totalImported} 个图块", "完成", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"导入失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    private void BtnSaveCatalog_Click(object sender, RoutedEventArgs e)
    {
        if (_blockManager == null)
        {
            MessageBox.Show("没有可保存的图块目录", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        try
        {
            _blockManager.Save();
            MessageBox.Show("图块目录已保存", "完成", MessageBoxButton.OK, MessageBoxImage.Information);
            Log($"目录已保存: {_blockManager.Blocks.Count} 个图块");
        }
        catch (Exception ex)
        {
            MessageBox.Show($"保存失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private void DgBlocks_SelectionChanged(object sender, System.Windows.Controls.SelectionChangedEventArgs e)
    {
        // 选中图块时可以显示详情（预留）
    }

    private void RefreshBlockDisplay()
    {
        if (_blockManager == null) return;

        _blockDisplayList = _blockManager.Blocks.Select(b => new BlockDisplayInfo
        {
            Name = b.Name,
            Description = b.Description,
            Attributes = b.Attributes,
            ExistsInDrawing = false // 默认未知，需刷新
        }).ToList();

        dgBlocks.ItemsSource = _blockDisplayList;
    }
}

/// <summary>
/// 图块显示信息
/// </summary>
public class BlockDisplayInfo
{
    public string Name { get; set; } = "";
    public string Description { get; set; } = "";
    public List<string> Attributes { get; set; } = new();
    public bool ExistsInDrawing { get; set; }
}

/// <summary>
/// 新建图块对话框
/// </summary>
public class CreateBlockDialog : Window
{
    public string BlockName { get; private set; } = "";
    public string Description { get; private set; } = "";

    private readonly TextBox _txtName;
    private readonly TextBox _txtDesc;

    public CreateBlockDialog()
    {
        Title = "新建回路图块";
        Width = 400;
        Height = 200;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;

        var panel = new StackPanel { Margin = new Thickness(16) };

        var namePanel = new StackPanel { Margin = new Thickness(0, 0, 0, 8) };
        namePanel.Children.Add(new TextBlock { Text = "图块名称:", Margin = new Thickness(0, 0, 0, 4) });
        _txtName = new TextBox { Text = "LOOP_POWER_C" };
        namePanel.Children.Add(_txtName);
        panel.Children.Add(namePanel);

        var descPanel = new StackPanel { Margin = new Thickness(0, 0, 0, 16) };
        descPanel.Children.Add(new TextBlock { Text = "描述:", Margin = new Thickness(0, 0, 0, 4) });
        _txtDesc = new TextBox { Text = "自定义回路图块" };
        descPanel.Children.Add(_txtDesc);
        panel.Children.Add(descPanel);

        var btnPanel = new StackPanel { Orientation = System.Windows.Controls.Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
        var okBtn = new Button { Content = "确定", Width = 80, Margin = new Thickness(0, 0, 8, 0) };
        okBtn.Click += (s, e) =>
        {
            BlockName = _txtName.Text.Trim().ToUpper();
            Description = _txtDesc.Text.Trim();
            if (string.IsNullOrEmpty(BlockName))
            {
                MessageBox.Show("请输入图块名称", "提示");
                return;
            }
            DialogResult = true;
        };
        var cancelBtn = new Button { Content = "取消", Width = 80 };
        cancelBtn.Click += (s, e) => DialogResult = false;
        btnPanel.Children.Add(okBtn);
        btnPanel.Children.Add(cancelBtn);
        panel.Children.Add(btnPanel);

        Content = panel;
    }
}
