package flash.events {
  public class InvokeEvent extends Event {
    public static const INVOKE:String = "invoke";
    public var arguments:Array;
    public var currentDirectory:Object;
    public function InvokeEvent(type:String, bubbles:Boolean=false, cancelable:Boolean=false, currentDirectory:Object=null, arguments:Array=null) {
      super(type, bubbles, cancelable);
      this.currentDirectory = currentDirectory;
      this.arguments = arguments || [];
    }
    public override function clone():Event {
      return new InvokeEvent(type, bubbles, cancelable, currentDirectory, arguments);
    }
  }
}
