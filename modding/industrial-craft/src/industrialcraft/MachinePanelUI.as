package industrialcraft {
 import assets.Images;
 import flash.display.BitmapData;
 import flash.display.DisplayObjectContainer;
 import flash.events.MouseEvent;
 import flash.geom.Rectangle;
 import orion.ui.UIStyle;
 import orion.ui.base.ButtonUI;
 import orion.ui.base.LabelUI;
 import orion.ui.base.PanelUI;
 import orion.ui.game.IInventoryUI;
 import orion.ui.game.ItemViewerUI;
 import orion.worlds.Item;
 import orion.worlds.ItemStack;
 public final class MachinePanelUI extends PanelUI implements IInventoryUI {
  private var state:MachineState;
  private var input:ItemViewerUI;
  private var output:ItemViewerUI;
  private var status:LabelUI;
  private var progress:LabelUI;
  private var toggle:ButtonUI;
  public function MachinePanelUI(parent:DisplayObjectContainer,state:MachineState){this.state=state;super(parent,327,34);}
  override protected function init():void{
   super.init();
   // Custom industrial panel, independent of the vanilla furnace artwork.
   var art:BitmapData=new BitmapData(301,460,true,0xff17252a);
   art.fillRect(new Rectangle(4,4,293,452),0xff34565b);
   art.fillRect(new Rectangle(9,9,283,442),0xff233a40);
   art.fillRect(new Rectangle(18,25,265,235),0xff172b30);
   art.fillRect(new Rectangle(21,28,259,229),0xff1d3539);
   art.fillRect(new Rectangle(54,101,40,40),0xffa77945);
   art.fillRect(new Rectangle(57,104,34,34),0xff101e20);
   art.fillRect(new Rectangle(204,101,40,40),0xffa77945);
   art.fillRect(new Rectangle(207,104,34,34),0xff101e20);
   art.fillRect(new Rectangle(76,191,149,16),0xff0d1c1d);
   art.fillRect(new Rectangle(79,194,143,10),0xff3a5752);
   art.fillRect(new Rectangle(12,270,277,2),0xffac824f);
   setImage(art);
  }
  override protected function addChildren():void {
   super.addChildren();
   input=new ItemViewerUI(this,58,105);input.setIndex(MachineState.INPUT);
   output=new ItemViewerUI(this,208,105);output.setIndex(MachineState.OUTPUT);
   new LabelUI(this,46,74).setAutoSize(false).setAlign(LabelUI.CENTER_ALIGN).setText("Сырьё").setSystemFont("Verdana",12,0xf0d29e).setSize(60,18);
   new LabelUI(this,196,74).setAutoSize(false).setAlign(LabelUI.CENTER_ALIGN).setText("Выход").setSystemFont("Verdana",12,0xf0d29e).setSize(60,18);
   new LabelUI(this,107,108).setAutoSize(false).setAlign(LabelUI.CENTER_ALIGN).setText("→").setSystemFont("Verdana",24,0x7ecdb8).setSize(86,34);
   status=new LabelUI(this,16,285).setAutoSize(false).setAlign(LabelUI.CENTER_ALIGN).setWordWrap(true).setSystemFont("Verdana",12,0xffffff).addFilter(UIStyle.BLACK_STROKE_FILTER).setSize(285,36) as LabelUI;
   progress=new LabelUI(this,16,321).setAutoSize(false).setAlign(LabelUI.CENTER_ALIGN).setSystemFont("Verdana",12,0x7ecdb8).addFilter(UIStyle.BLACK_STROKE_FILTER).setSize(285,22) as LabelUI;
   toggle=new ButtonUI(this,97,350).setText("Запустить").setTextSystemFont("Verdana",13,0xffffff).setTextFontBold(true).setTextFilters(UIStyle.BLACK_STROKE_FILTER).setImage(Images.BUTTON_GAME_INVENTORY_GREEN_BIG).setMargin(0,2).setSize(122,59) as ButtonUI;
   new LabelUI(this,8,414).setAutoSize(false).setAlign(LabelUI.CENTER_ALIGN).setWordWrap(true).setVerticalAlign(LabelUI.MIDDLE_ALIGN).setSystemFont("Verdana",10,0xffffff).setText("1 смола → 1 модуль за 5 с. Закройте панель, чтобы механизм работал.").addFilter(UIStyle.BLACK_STROKE_FILTER).setSize(299,38);
   refresh();
  }
  override protected function addEventListeners():void{super.addEventListeners();toggle.addEventListener(MouseEvent.CLICK,onToggle);}
  override protected function removeEventListeners():void{super.removeEventListeners();toggle.removeEventListener(MouseEvent.CLICK,onToggle);}
  override protected function draw():void {
   super.draw();
   if(state.progress>0){
    graphics.beginFill(0x70d9b7);graphics.drawRect(79,194,143*state.progress/MachineState.WORK_TICKS,10);graphics.endFill();
   }
  }
  private function onToggle(e:MouseEvent):void{state.running=!state.running;refresh();}
  public function refresh():void {
   input.updateNow();output.updateNow();
   var text:String="Ожидание смолы";
   if(state.running)text=state.canRun()?"Калибровка…":"Нет сырья или выход заполнен";
   else if(state.progress>0)text="Пауза";
   status.text=text;progress.text="Прогресс: "+state.progress+"/"+MachineState.WORK_TICKS+"   Готово: "+state.completed;
   toggle.setText(state.running?"Остановить":"Запустить");
   invalidate();
  }
  public function canSetItem(viewer:ItemViewerUI,stack:ItemStack):Boolean {
   if(stack==null)return true;
   if(viewer.index==MachineState.INPUT)return stack.item==Item.RESIN;
   return false;
  }
  public function setItem(viewer:ItemViewerUI,stack:ItemStack):void{state.items[viewer.index]=stack;refresh();}
  public function getItem(index:int):ItemStack{return state.items[index];}
 }
}
