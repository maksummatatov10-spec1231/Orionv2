package industrialcraft {
 import flash.utils.Dictionary;
 import flash.utils.ByteArray;
 import orion.worlds.Block;
 import orion.worlds.ItemStack;
 import orion.worlds.World;
 public final class MachineManager {
  private static var machines:Dictionary=new Dictionary();
  private static var world:World;
  private static var accumulator:int=0;
  public static const TICK_MS:int=1000;
  public static function bind(w:World,clear:Boolean=true):void {
   if(world==w && !clear)return;
   world=w;machines=new Dictionary();accumulator=0;
  }
  public static function key(x:int,y:int):String{return x+","+y;}
  public static function getOrCreate(x:int,y:int):MachineState {
   if(world==null || world.tiles[x+y*world.tilesX].blockId!=ContentRegistry.PROBE_BLOCK.id)throw new Error("IC: станок без блока");
   var k:String=key(x,y);var s:MachineState=machines[k] as MachineState;
   if(s==null){s=new MachineState(x,y);machines[k]=s;}
   return s;
  }
  public static function get(x:int,y:int):MachineState{return machines[key(x,y)] as MachineState;}
  public static function addLoaded(s:MachineState):void {
   if(world==null)throw new Error("IC: мир не привязан");
   if(get(s.x,s.y)!=null)throw new Error("IC: дубликат состояния станка");
   machines[key(s.x,s.y)]=s;
  }
  public static function removed(x:int,y:int,drop:Boolean):void {
   var s:MachineState=get(x,y);if(s==null)return;
   if(drop && world!=null){
    for each(var stack:ItemStack in s.items)if(stack!=null && stack.count>0)world.dropTileEntityItem(x,y,stack);
   }
   delete machines[key(x,y)];
   s.items[0]=null;s.items[1]=null;s.running=false;
  }
  public static function update(deltaMs:int):void {
   if(world==null || Context.game==null || Context.game.gameLoopPause || !world.created)return;
   accumulator+=deltaMs;
   while(accumulator>=TICK_MS){accumulator-=TICK_MS;tickOnce();}
  }
  public static function tickOnce():void {
   for each(var s:MachineState in machines){
    var tile:* = world.tiles[s.x+s.y*world.tilesX];
    if(tile.blockId!=ContentRegistry.PROBE_BLOCK.id){removed(s.x,s.y,false);continue;}
    s.tick();
   }
  }
  public static function save(out:ByteArray):void {
   var list:Vector.<MachineState>=new Vector.<MachineState>();
   for each(var s:MachineState in machines)list.push(s);
   list.sort(function(a:MachineState,b:MachineState):int{var ka:int=a.y*world.tilesX+a.x;var kb:int=b.y*world.tilesX+b.x;return ka-kb;});
   out.writeInt(list.length);for each(s in list)s.save(out);
  }
  public static function load(input:ByteArray):void {
   var count:int=input.readInt();if(count<0 || count>world.tilesX*world.tilesY)throw new Error("IC: неверное число станков");
   for(var i:int=0;i<count;i++){
    var s:MachineState=MachineState.load(input);
    if(s.x<0 || s.y<0 || s.x>=world.tilesX || s.y>=world.tilesY)throw new Error("IC: станок вне мира");
    if(world.tiles[s.x+s.y*world.tilesX].blockId!=ContentRegistry.PROBE_BLOCK.id)throw new Error("IC: станок без блока");
    addLoaded(s);
   }
  }
  public static function count():int{var n:int=0;for each(var s:MachineState in machines)n++;return n;}
 }
}
