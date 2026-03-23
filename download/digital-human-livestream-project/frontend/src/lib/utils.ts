import { clsx, type ClassArray, type ClassDictionary, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: (ClassArray | ClassDictionary | ClassValue | undefined | null)[]) {
  return twMerge(clsx(inputs));
}
