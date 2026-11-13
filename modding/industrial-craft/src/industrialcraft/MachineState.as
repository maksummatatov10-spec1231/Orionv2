package industrialcraft {
 import flash.utils.ByteArray;
 import orion.worlds.Item;
 import orion.worlds.ItemStack;
 public final class MachineState {
  public static const TYPE_PROBE:int=1;
  public static const INPUT:int=0;
  public static const OUTPUT:int=1;
  public static const WORK_TICKS:int=5;
  public var type:int=TYPE_PROBE;
  public var x:int; public var y:int;
  public var items:Vector.<ItemStack>=new Vector.<ItemStack>(2,true);
  public var progress:int=0;
  public var completed:int=0;
  public var running:Boolean=false;
  public function MachineState(x:int=0,y:int=0){this.x=x;this.y=y;}
  public function canRun():Boolean {
   var input:ItemStack=items[INPUT]; var output:ItemStack=items[OUTPUT];
   if(input==null || input.item!=Item.RESIN || input.count<1)return false;
   if(output!=null && (output.item!=ContentRegistry.PROBE || output.count>=output.item.maxStackSize))return false;
   return true;
  }
  public function tick():Boolean {
   if(!running)return false;
   if(!canRun()){running=false;return true;}
   progress++;
   if(progress>=WORK_TICKS){
    progress=0; items[INPUT].count--;
    if(items[INPUT].count<=0)items[INPUT]=null;
    if(items[OUTPUT]==null)items[OUTPUT]=new ItemStack(ContentRegistry.PROBE,0,1);
    else items[OUTPUT].count++;
    completed++;
    if(!canRun())running=false;
   }
   return true;
  }
  public function save(out:ByteArray):void {
   out.writeInt(type);out.writeInt(x);out.writeInt(y);out.writeInt(progress);out.writeInt(completed);out.writeBoolean(running);
   ItemStack.save(out,items[INPUT]);ItemStack.save(out,items[OUTPUT]);
  }
  public static function load(input:ByteArray):MachineState {
   var s:MachineState=new MachineState();s.type=input.readInt();s.x=input.readInt();s.y=input.readInt();s.progress=input.readInt();s.completed=input.readInt();s.running=input.readBoolean();
   s.items[INPUT]=ItemStack.load(input);s.items[OUTPUT]=ItemStack.load(input);
   if(s.type!=TYPE_PROBE || s.progress<0 || s.progress>=WORK_TICKS || s.completed<0)throw new Error("IC: повреждено состояние станка");
   var loadedInput:ItemStack=s.items[INPUT];var loadedOutput:ItemStack=s.items[OUTPUT];
   if(loadedInput!=null && (loadedInput.item!=Item.RESIN || loadedInput.count<0 || loadedInput.count>loadedInput.item.maxStackSize))throw new Error("IC: повреждён входной слот");
   if(loadedOutput!=null && (loadedOutput.item!=ContentRegistry.PROBE || loadedOutput.count<0 || loadedOutput.count>loadedOutput.item.maxStackSize))throw new Error("IC: повреждён выходной слот");
   return s;
  }
 }
}
