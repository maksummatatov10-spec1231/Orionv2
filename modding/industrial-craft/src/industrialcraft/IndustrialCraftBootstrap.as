package industrialcraft {
 import flash.events.Event;
 import flash.events.TimerEvent;
 import flash.utils.ByteArray;
 import flash.utils.Timer;
 import flash.utils.getTimer;
 import orion.events.DialogEvent;
 import orion.worlds.World;
 public final class IndustrialCraftBootstrap {
  public static const VERSION:String="0.1.0-stage0";
  public static const SAVE_MAGIC:uint=0x49435731; // ICW1
  public static const SAVE_VERSION:int=1;
  private static var installed:Boolean=false;
  private static var timer:Timer;
  private static var lastTime:int=0;
  private static var dialog:MachineDialogUI;
  public static function install():void {
   if(installed)return;
   ContentRegistry.install();
   lastTime=getTimer();timer=new Timer(100);timer.addEventListener(TimerEvent.TIMER,onTimer);timer.start();
   installed=true;trace("IC_BOOTSTRAP_READY "+VERSION);
  }
  private static function onTimer(e:TimerEvent):void {
   var now:int=getTimer();var delta:int=now-lastTime;lastTime=now;
   if(delta<0 || delta>1000)delta=100;
   if(Context.world!=null)MachineManager.bind(Context.world,false);
   MachineManager.update(delta);
  }
  public static function saveWorld(world:World,out:ByteArray):void {
   MachineManager.bind(world,false);
   out.writeUnsignedInt(SAVE_MAGIC);out.writeInt(SAVE_VERSION);out.writeInt(ContentRegistry.PROBE_ID);MachineManager.save(out);
   trace("IC_SAVE machines="+MachineManager.count());
  }
  public static function loadWorld(world:World,input:ByteArray):void {
   MachineManager.bind(world,true);
   if(input.bytesAvailable<4)return;
   var start:uint=input.position;var magic:uint=input.readUnsignedInt();
   if(magic!=SAVE_MAGIC){input.position=start;trace("IC_LOAD_LEGACY_WORLD");return;}
   var version:int=input.readInt();var contentId:int=input.readInt();
   if(version!=SAVE_VERSION || contentId!=ContentRegistry.PROBE_ID)throw new Error("IC: версия сохранения не поддерживается");
   MachineManager.load(input);trace("IC_LOAD machines="+MachineManager.count());
  }
  public static function openMachine(x:int,y:int):void {
   var state:MachineState=MachineManager.getOrCreate(x,y);
   Context.game.gameLoopPause=true;
   dialog=new MachineDialogUI(Context.app,state);
   dialog.addEventListener(DialogEvent.CLOSED,onClosed);dialog.show();
   trace("IC_PANEL_OPEN "+x+","+y);
  }
  private static function onClosed(e:DialogEvent):void {
   dialog.removeEventListener(DialogEvent.CLOSED,onClosed);dialog.dispose();dialog=null;
   Context.game.gameLoopPause=false;Context.game.controller.resetCursor();
   trace("IC_PANEL_CLOSED");
  }
 }
}
