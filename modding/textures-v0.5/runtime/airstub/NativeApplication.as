package flash.desktop {
  import flash.events.EventDispatcher;
  public class NativeApplication extends EventDispatcher {
    private static var _instance:NativeApplication;
    public static function get nativeApplication():NativeApplication {
      if (!_instance) _instance = new NativeApplication();
      return _instance;
    }
    public function NativeApplication() { super(); }
    public function exit(code:int = 0):void {}
  }
}
