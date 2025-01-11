import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TradesWithOrderInfoComponent } from './trades-with-order-info.component';

describe('TradesWithOrderInfoComponent', () => {
  let component: TradesWithOrderInfoComponent;
  let fixture: ComponentFixture<TradesWithOrderInfoComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TradesWithOrderInfoComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TradesWithOrderInfoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
