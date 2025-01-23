import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SuspensionsComponent } from './suspensions.component';

describe('SuspensionsComponent', () => {
  let component: SuspensionsComponent;
  let fixture: ComponentFixture<SuspensionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SuspensionsComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SuspensionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
