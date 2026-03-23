import * as React from "react"
import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

const cn = (...inputs: (string | boolean | undefined)[]) => {
  return twMerge(clsx(...inputs))
}

// Button component
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "danger" | "secondary";
  size?: "default" | "sm";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", disabled, ...props }, ref) => {
    const baseClasses = "inline-flex items-center justify-center rounded-lg font-medium transition-colors focus-visible:outline-none"
    const variantClasses: Record<string, string> = {
      default: "bg-green-600 text-white hover:bg-green-700",
      danger: "bg-red-600 text-white hover:bg-red-700",
      secondary: "bg-gray-600 text-white hover:bg-gray-700",
    }
    const sizeClasses: Record<string, string> = {
      default: "h-10 px-4",
      sm: "h-8 px-3 text-sm",
    }
    
    return (
      <button
        className={cn(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          disabled && "opacity-50 cursor-not-allowed",
          className
        )}
        ref={ref}
        disabled={disabled}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

// Card component
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, title, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "bg-gray-800/30 border border-gray-700 rounded-lg overflow-hidden",
          className
        )}
        {...props}
      >
        {title && (
          <div className="px-3 border-b border-gray-700">
            <h3 className="text-lg font-bold text-white">{title}</h3>
          </div>
        )}
        {children}
      </div>
    )
  }
)
Card.displayName = "Card"
