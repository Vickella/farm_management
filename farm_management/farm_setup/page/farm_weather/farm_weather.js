frappe.pages['farm-weather'].on_page_load = function(wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Farm Weather Forecast',
		single_column: true
	});

	frappe.farm_weather_page = new FarmWeatherPage(page, wrapper);
};

class FarmWeatherPage {
	constructor(page, wrapper) {
		this.page = page;
		this.wrapper = wrapper;
		this.selected_farm = null;
		this.setup();
	}

	setup() {
		this.add_farm_selector();
		this.render_empty_state();
	}

	add_farm_selector() {
		const me = this;
		this.page.add_field({
			fieldtype: 'Link',
			fieldname: 'farm',
			options: 'Farm',
			label: 'Select Farm',
			change() {
				const farm = this.get_value();
				if (farm) {
					me.selected_farm = farm;
					me.load_weather(farm);
				}
			}
		});

		this.page.add_button('Refresh', () => {
			if (me.selected_farm) me.load_weather(me.selected_farm);
		}, { icon: 'refresh' });
	}

	load_weather(farm_name) {
		const me = this;
		$(this.wrapper).find('.weather-content').remove();
		const loading = $(`
			<div class="weather-content text-center" style="padding:60px">
				<div class="spinner-border text-primary" role="status"></div>
				<p class="mt-3 text-muted">Fetching weather data...</p>
			</div>
		`).appendTo($(this.wrapper).find('.page-content'));

		frappe.call({
			method: 'farm_management.farm_management.api.weather.get_farm_weather',
			args: { farm_name: farm_name },
			callback(r) {
				loading.remove();
				if (r.message) {
					me.render_weather(r.message);
				} else {
					me.render_error('No weather data received.');
				}
			},
			error(r) {
				loading.remove();
				me.render_error(me.get_error_message(r));
			}
		});
	}

	get_error_message(r) {
		const fallback = 'Failed to fetch weather. Check Farm location and API key in Farm Management Settings.';
		const response = (r && r.responseJSON) || {};
		let message = response.message || response.exception || fallback;

		if (response._server_messages) {
			try {
				const server_messages = JSON.parse(response._server_messages);
				if (server_messages.length) {
					message = JSON.parse(server_messages[0]).message || message;
				}
			} catch (e) {
				// Keep the fallback message if Frappe returns an unexpected error shape.
			}
		}

		return message;
	}

	render_weather(data) {
		$(this.wrapper).find('.weather-content').remove();
		const current = data.current || {};
		const forecast = data.forecast || [];
		const wind_dir = this.wind_direction(current.wind_deg);

		const current_html = `
		<div style="background:linear-gradient(135deg,#001f33,#0d6efd);border-radius:16px;padding:28px;color:#fff;margin-bottom:20px">
			<div class="row align-items-center">
				<div class="col-md-4 text-center">
					<img src="${current.icon_url || ''}" style="width:80px">
					<div style="font-size:48px;font-weight:800">${current.temperature !== undefined ? current.temperature.toFixed(1) : '--'}${current.unit_symbol || ''}</div>
					<div style="font-size:18px;opacity:0.9">${current.description || ''}</div>
					<div style="opacity:0.7;margin-top:6px">Feels like ${current.feels_like !== undefined ? current.feels_like.toFixed(1) : '--'}${current.unit_symbol || ''}</div>
				</div>
				<div class="col-md-4 text-center">
					<div style="font-size:22px;font-weight:700;margin-bottom:10px">${data.location || ''}</div>
					<table style="width:100%;color:rgba(255,255,255,0.9);font-size:15px">
						<tr><td>Humidity</td><td><b>${current.humidity || '--'}%</b></td></tr>
						<tr><td>Wind</td><td><b>${current.wind_speed || '--'} ${current.wind_unit || 'm/s'} ${wind_dir}</b></td></tr>
						<tr><td>Pressure</td><td><b>${current.pressure || '--'} hPa</b></td></tr>
						<tr><td>UV Index</td><td><b>${current.uvi !== undefined ? current.uvi.toFixed(1) : '--'}</b></td></tr>
						<tr><td>Cloud Cover</td><td><b>${current.clouds || '--'}%</b></td></tr>
						<tr><td>Visibility</td><td><b>${current.visibility ? (current.visibility / 1000).toFixed(1) + ' km' : '--'}</b></td></tr>
					</table>
				</div>
				<div class="col-md-4 text-center">
					<div style="font-size:14px;opacity:0.8;margin-bottom:16px">AGRICULTURAL ADVISORY</div>
					${this.get_advisory_html(current)}
				</div>
			</div>
		</div>`;

		const forecast_cards = forecast.map(day => {
			const date = new Date(day.dt * 1000);
			const day_name = date.toLocaleDateString('en', { weekday: 'short', month: 'short', day: 'numeric' });
			const rain_risk = day.pop > 60 ? 'High Rain Risk' : (day.pop > 30 ? 'Possible Rain' : 'Low Rain Risk');
			return `
			<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;text-align:center;min-width:140px;flex:0 0 auto">
				<div style="font-weight:700;color:#031a33;margin-bottom:8px;font-size:13px">${day_name}</div>
				<img src="${day.icon_url}" style="width:44px">
				<div style="font-size:14px;color:#64748b;margin:6px 0">${day.description || ''}</div>
				<div style="font-size:18px;font-weight:800;color:#031a33">${day.temp_max !== undefined ? day.temp_max.toFixed(0) : '--'}${day.unit_symbol || ''}</div>
				<div style="font-size:13px;color:#94a3b8">Low: ${day.temp_min !== undefined ? day.temp_min.toFixed(0) : '--'}${day.unit_symbol || ''}</div>
				<div style="font-size:12px;color:#0d6efd;margin-top:6px">${day.pop || 0}% rain</div>
				<div style="font-size:11px;color:#64748b;margin-top:4px">${rain_risk}</div>
				<div style="font-size:11px;color:#64748b">Wind ${day.wind_speed || '--'} m/s</div>
				<div style="font-size:11px;color:#64748b">Clouds ${day.clouds || '--'}%</div>
			</div>`;
		}).join('');

		const html = `
		<div class="weather-content" style="padding:20px">
			${current_html}
			<h6 style="color:#031a33;font-weight:700;margin-bottom:14px">5-Day Forecast</h6>
			<div style="display:flex;gap:12px;overflow-x:auto;padding-bottom:10px">
				${forecast_cards || '<p class="text-muted">No forecast data available.</p>'}
			</div>
		</div>`;

		$(html).appendTo($(this.wrapper).find('.page-content'));
	}

	get_advisory_html(current) {
		const tips = [];
		if (current.uvi > 8) tips.push('Extreme UV - avoid midday fieldwork');
		else if (current.uvi > 5) tips.push('High UV - protect workers');
		if (current.wind_speed > 7) tips.push('High wind - avoid spraying');
		else if (current.wind_speed < 3) tips.push('Low wind - good for spraying');
		if (current.humidity > 85) tips.push('High humidity - watch for fungal disease');
		if (current.humidity < 35) tips.push('Low humidity - monitor crops for stress');
		if (current.clouds > 80) tips.push('Overcast - low evapotranspiration');
		if (!tips.length) tips.push('Conditions normal for fieldwork');
		return tips.map(t => `<div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 12px;margin:6px 0;font-size:13px;text-align:left">${t}</div>`).join('');
	}

	wind_direction(deg) {
		if (deg === undefined) return '';
		const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
		return dirs[Math.round(deg / 45) % 8];
	}

	render_empty_state() {
		$(`<div class="weather-content text-center" style="padding:80px">
			<div style="font-size:64px;color:#cbd5e1">Cloud</div>
			<p class="mt-3 text-muted">Select a farm above to view weather forecast</p>
		</div>`).appendTo($(this.wrapper).find('.page-content'));
	}

	render_error(msg) {
		$(`<div class="weather-content text-center" style="padding:60px">
			<div style="font-size:48px;color:#ef4444">!</div>
			<p class="mt-3 text-muted">${msg}</p>
		</div>`).appendTo($(this.wrapper).find('.page-content'));
	}
}
