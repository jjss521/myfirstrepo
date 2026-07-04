namespace PDSG.Core.Exceptions;

/// <summary>
/// PDSG 基础异常类
/// </summary>
public class PdsgException : Exception
{
    public PdsgException(string message) : base(message) { }
    public PdsgException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>
/// Excel 文件读取异常
/// </summary>
public class ExcelReadException : PdsgException
{
    public ExcelReadException(string message) : base(message) { }
    public ExcelReadException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>
/// 配置文件加载异常
/// </summary>
public class ConfigException : PdsgException
{
    public ConfigException(string message) : base(message) { }
    public ConfigException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>
/// 图块库异常
/// </summary>
public class BlockLibraryException : PdsgException
{
    public BlockLibraryException(string message) : base(message) { }
    public BlockLibraryException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>
/// AutoCAD 连接异常
/// </summary>
public class AcadConnectionException : PdsgException
{
    public AcadConnectionException(string message) : base(message) { }
    public AcadConnectionException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>
/// AutoCAD 操作异常
/// </summary>
public class AcadOperationException : PdsgException
{
    public AcadOperationException(string message) : base(message) { }
    public AcadOperationException(string message, Exception inner) : base(message, inner) { }
}

/// <summary>
/// 单个回路数据校验异常（不导致程序退出）
/// </summary>
public class CircuitValidationException : PdsgException
{
    public CircuitValidationException(string message) : base(message) { }
}
