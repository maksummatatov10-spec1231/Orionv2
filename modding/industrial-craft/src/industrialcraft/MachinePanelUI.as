package industrialcraft {
 import assets.Images;
 import flash.display.BitmapData;
 import flash.display.DisplayObjectContainer;
 import flash.events.MouseEvent;
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
  private var progressImage:BitmapData;
  public function MachinePanelUI(parent:DisplayObjectContainer,state:MachineState){this.state=state;super(parent,327,34);}
  override protected function init():void{
   super.init();
   setImage(Images.FURNACE_BACKGROUND);
   progressImage=Images.FURNACE_PROGRESS;
  }
  override protected function addChildren():void {
   super.addChildren();
   input=new ItemViewerUI(this,58,92);input.setIndex(MachineState.INPUT);
   output=new ItemViewerUI(this,208,163);output.setIndex(MachineState.OUTPUT);
   new LabelUI(this,112,99).setAutoSize(false).setAlign(LabelUI.LEFT_ALIGN).setText("Сырьё").setSystemFont("Verdana",12,0x003666).addFilter(UIStyle.GRAY_SHADOW_FILTER).setSize(100,18);
   new LabelUI(this,208,140).setAutoSize(false).setAlign(LabelUI.CENTER_ALIGN).setText("Выход").setSystemFont("Verdana",12,0x003666).addFilter(UIStyle.GRAY_SHADOW_FILTER).setSize(60,18);
   new LabelUI(this,58,238).setAutoSize(false).setAlign(LabelUI.CENTER_ALIGN).setText("—").setSystemFont("Verdana",14,0x003666).setSize(50,20);
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
   if(progressImage!=null && state.progress>0){
    var ratio:Number=state.progress/MachineState.WORK_TICKS;
    drawImageEx(progressImage,90,143,0,0,progressImage.width*ratio,progressImage.height);
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
