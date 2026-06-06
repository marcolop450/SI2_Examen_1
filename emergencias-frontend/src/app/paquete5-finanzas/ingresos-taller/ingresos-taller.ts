import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PagoService } from '../../core/services/pago';

@Component({
  selector: 'app-ingresos-taller',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ingresos-taller.html',
  styleUrls: ['./ingresos-taller.css']
})
export class IngresosTallerComponent implements OnInit {
  pagos: any[] = [];
  cargando: boolean = true;

  constructor(private pagoService: PagoService) {}

  ngOnInit(): void {
    this.cargarMisIngresos();
  }

  cargarMisIngresos(): void {
    this.cargando = true;
    
    this.pagoService.obtenerMisIngresos().subscribe({
      next: (data) => {
        this.pagos = data;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error al cargar ingresos:', err);
        this.cargando = false;
      }
    });
  }

  get totalIngresosBrutos(): number {
    return this.pagos.reduce((acc, pago) => acc + parseFloat(pago.monto_total_decimal), 0);
  }

  get totalComisionAPagar(): number {
    return this.pagos.reduce((acc, pago) => acc + parseFloat(pago.comision_plataforma_decimal), 0);
  }

  get gananciaNeta(): number {
    return this.totalIngresosBrutos - this.totalComisionAPagar;
  }
}
