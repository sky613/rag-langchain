type ClassValue = string | false | null | undefined;

export function cn(...values: ClassValue[]) {
  // 조건부 Tailwind 클래스를 간단히 합치기 위한 경량 className 헬퍼다.
  return values.filter(Boolean).join(" ");
}
