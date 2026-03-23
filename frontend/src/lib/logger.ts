/**
 * Error Logging Utility
 * Provides centralized error handling and logging for the frontend
 */

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  FATAL = 'fatal',
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
  error?: Error;
  stack?: string;
  url?: string;
  userAgent?: string;
}

class Logger {
  private static instance: Logger;
  private logs: LogEntry[] = [];
  private maxLogs = 1000;
  private apiUrl: string;
  private isProduction: boolean;
  private sessionId: string;

  private constructor() {
    this.apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    this.isProduction = process.env.NODE_ENV === 'production';
    this.sessionId = this.generateSessionId();
    
    // Setup global error handlers
    this.setupGlobalHandlers();
  }

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupGlobalHandlers(): void {
    // Handle uncaught errors
    if (typeof window !== 'undefined') {
      window.onerror = (message, source, lineno, colno, error) => {
        this.fatal('Uncaught Error', {
          message: String(message),
          source,
          lineno,
          colno,
        }, error);
        return false;
      };

      // Handle unhandled promise rejections
      window.onunhandledrejection = (event) => {
        this.error('Unhandled Promise Rejection', {
          reason: String(event.reason),
        }, event.reason instanceof Error ? event.reason : undefined);
      };
    }
  }

  private createLogEntry(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>,
    error?: Error
  ): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
      error,
      stack: error?.stack,
      url: typeof window !== 'undefined' ? window.location.href : undefined,
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
    };
  }

  private addLog(entry: LogEntry): void {
    this.logs.push(entry);
    
    // Trim old logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }
  }

  private async sendToServer(entry: LogEntry): Promise<void> {
    if (!this.isProduction) return;

    try {
      await fetch(`${this.apiUrl}/api/v1/logs/frontend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...entry,
          sessionId: this.sessionId,
        }),
      });
    } catch {
      // Silently fail - don't cause infinite error loops
    }
  }

  private log(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>,
    error?: Error
  ): void {
    const entry = this.createLogEntry(level, message, context, error);
    this.addLog(entry);

    // Console output in development
    if (!this.isProduction) {
      const consoleMethod = level === LogLevel.FATAL ? 'error' : level;
      const prefix = `[${entry.timestamp}] [${level.toUpperCase()}]`;
      
      if (error) {
        console[consoleMethod](prefix, message, context || '', error);
      } else {
        console[consoleMethod](prefix, message, context || '');
      }
    }

    // Send errors and fatals to server
    if (level === LogLevel.ERROR || level === LogLevel.FATAL) {
      this.sendToServer(entry);
    }
  }

  debug(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  info(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.INFO, message, context);
  }

  warn(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.WARN, message, context);
  }

  error(message: string, context?: Record<string, unknown>, error?: Error): void {
    this.log(LogLevel.ERROR, message, context, error);
  }

  fatal(message: string, context?: Record<string, unknown>, error?: Error): void {
    this.log(LogLevel.FATAL, message, context, error);
  }

  // API Error handler
  apiError(endpoint: string, status: number, message: string, error?: Error): void {
    this.error(`API Error: ${endpoint}`, {
      endpoint,
      status,
      responseMessage: message,
    }, error);
  }

  // Component error handler
  componentError(componentName: string, error: Error, props?: Record<string, unknown>): void {
    this.error(`Component Error: ${componentName}`, {
      componentName,
      props: this.sanitizeProps(props),
    }, error);
  }

  // Sanitize props to remove sensitive data
  private sanitizeProps(props?: Record<string, unknown>): Record<string, unknown> {
    if (!props) return {};
    
    const sanitized: Record<string, unknown> = {};
    const sensitiveKeys = ['password', 'token', 'secret', 'key', 'auth'];
    
    for (const [key, value] of Object.entries(props)) {
      if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk))) {
        sanitized[key] = '[REDACTED]';
      } else if (typeof value === 'object' && value !== null) {
        sanitized[key] = this.sanitizeProps(value as Record<string, unknown>);
      } else {
        sanitized[key] = value;
      }
    }
    
    return sanitized;
  }

  // Get all logs for debugging
  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  // Get logs by level
  getLogsByLevel(level: LogLevel): LogEntry[] {
    return this.logs.filter(log => log.level === level);
  }

  // Export logs as JSON
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  // Clear logs
  clearLogs(): void {
    this.logs = [];
  }

  // Get session ID
  getSessionId(): string {
    return this.sessionId;
  }
}

// Export singleton instance
export const logger = Logger.getInstance();

// React Error Boundary helper
export function logReactError(
  error: Error,
  errorInfo: { componentStack?: string | null },
  componentName?: string
): void {
  logger.error('React Error Boundary Caught', {
    componentName,
    componentStack: errorInfo.componentStack || undefined,
  }, error);
}

// API fetch wrapper with error logging
export async function loggedFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const startTime = Date.now();
  
  try {
    const response = await fetch(endpoint, options);
    const duration = Date.now() - startTime;
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      logger.apiError(endpoint, response.status, errorText);
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }
    
    logger.debug(`API Success: ${endpoint}`, { duration: `${duration}ms` });
    
    return response.json();
  } catch (error) {
    const duration = Date.now() - startTime;
    logger.apiError(
      endpoint,
      0,
      error instanceof Error ? error.message : 'Unknown error',
      error instanceof Error ? error : undefined
    );
    throw error;
  }
}
