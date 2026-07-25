export {};

declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string;
        ready(): void;
        expand(): void;
        HapticFeedback?: {
          notificationOccurred(type: 'success' | 'error'): void;
        };
      };
    };
  }
}
